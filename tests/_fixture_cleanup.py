"""Test-only scratch cleanup. No production store API imports or mutations."""
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
from pathlib import Path
import stat
import tarfile
import shutil
import uuid
from importlib.metadata import version
import sys
import time


class CleanupError(OSError):
    pass


def identity(path):
    info = Path(path).lstat()
    return [info.st_dev, info.st_ino, info.st_uid]


def private_path(path):
    path = Path(path).absolute()
    if '..' in path.parts:
        raise CleanupError('parent traversal')
    for part in (path, *path.parents):
        if part.is_symlink():
            raise CleanupError('symlink ancestor')
    return path


def mounts_below(path):
    root = str(private_path(path))
    found = []
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        value = line.split()[4]
        for escape, char in ((r'\040', ' '), (r'\011', '\t'), (r'\012', '\n'), (r'\134', '\\')):
            value = value.replace(escape, char)
        if value == root or value.startswith(root + '/'):
            found.append(value)
    return found


def busy(path, *, strict=False):
    """Additional observer for owned fixtures; shared legacy audits use strict.

    Owned fixtures rely on registration, completed phases and resource closure.
    An unrelated nondumpable host process cannot disprove that lifecycle. Shared
    paths have no such ownership proof and reject incomplete observation.
    """
    root = str(private_path(path))
    for line in Path('/proc/net/unix').read_text().splitlines()[1:]:
        fields = line.split(None, 7)
        if len(fields) == 8 and (fields[7] == root or fields[7].startswith(root+'/')):
            return True
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            if process.stat().st_uid != os.getuid():
                continue
            links = [process/'cwd', process/'root', *list((process/'fd').iterdir())]
            for link in links:
                try:
                    value = os.readlink(link).removesuffix(' (deleted)')
                except FileNotFoundError:
                    continue
                if value == root or value.startswith(root + '/'):
                    return True
        except FileNotFoundError:
            continue
        except PermissionError as exc:
            if strict:
                raise CleanupError('cannot inspect same-UID process users') from exc
    return False


def inventory(path, expected=None):
    """No symlink traversal; reject mounts/foreign owners before any chmod."""
    path = private_path(path)
    observed = identity(path)
    if expected is not None and observed != expected:
        raise CleanupError('root identity changed')
    if observed[2] != os.getuid() or mounts_below(path):
        raise CleanupError('foreign owner or mounted root')
    entries = []

    def visit(fd, relative):
        here = os.fstat(fd)
        if here.st_uid != os.getuid() or here.st_dev != observed[0]:
            raise CleanupError('foreign owner or device')
        entries.append((relative, here))
        for name in sorted(os.listdir(fd)):
            info = os.stat(name, dir_fd=fd, follow_symlinks=False)
            child = relative/name
            if info.st_uid != os.getuid() or info.st_dev != observed[0]:
                raise CleanupError('foreign owner or device')
            if stat.S_ISDIR(info.st_mode):
                child_fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                try:
                    if (os.fstat(child_fd).st_dev, os.fstat(child_fd).st_ino) != (info.st_dev, info.st_ino):
                        raise CleanupError('directory replaced')
                    visit(child_fd, child)
                finally:
                    os.close(child_fd)
            elif any(check(info.st_mode) for check in (stat.S_ISREG,stat.S_ISLNK,stat.S_ISSOCK,stat.S_ISFIFO)):
                entries.append((child, info))
            else:
                raise CleanupError('special file still present')

    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        if list((os.fstat(fd).st_dev, os.fstat(fd).st_ino, os.fstat(fd).st_uid)) != observed:
            raise CleanupError('root replaced')
        visit(fd, Path('.'))
    finally:
        os.close(fd)
    return entries


def remove_owned_tree(path, expected):
    """Restore directory owner permissions only; unlink aliases without following."""
    path = private_path(path)
    registered = dict(inventory(path, expected))
    if busy(path):
        raise CleanupError('scratch still in use')
    parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        def remove(directory, name, wanted, relative):
            info = os.stat(name, dir_fd=directory, follow_symlinks=False)
            if (info.st_dev, info.st_ino, info.st_uid) != tuple(wanted):
                raise CleanupError('object identity changed')
            fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            try:
                here = os.fstat(fd)
                if (here.st_dev, here.st_ino, here.st_uid) != tuple(wanted):
                    raise CleanupError('directory replaced')
                os.fchmod(fd, stat.S_IMODE(here.st_mode) | stat.S_IRWXU)
                for child in os.listdir(fd):
                    item = os.stat(child, dir_fd=fd, follow_symlinks=False)
                    original = registered.get(relative/child)
                    if original is None or (item.st_dev, item.st_ino, item.st_uid, item.st_mode) != (
                            original.st_dev, original.st_ino, original.st_uid, original.st_mode):
                        raise CleanupError('child identity changed')
                    if not stat.S_ISDIR(item.st_mode) and (item.st_size, item.st_mtime_ns) != (
                            original.st_size, original.st_mtime_ns):
                        raise CleanupError('child contents changed')
                    if item.st_uid != os.getuid() or item.st_dev != wanted[0]:
                        raise CleanupError('foreign owner or device')
                    if stat.S_ISDIR(item.st_mode):
                        remove(fd, child, (item.st_dev, item.st_ino, item.st_uid), relative/child)
                    elif any(check(item.st_mode) for check in (stat.S_ISREG,stat.S_ISLNK,stat.S_ISSOCK,stat.S_ISFIFO)):
                        os.unlink(child, dir_fd=fd)
                    else:
                        raise CleanupError('special file still present')
                current = os.stat(name, dir_fd=directory, follow_symlinks=False)
                if (current.st_dev, current.st_ino, current.st_uid) != tuple(wanted):
                    raise CleanupError('directory replaced before unlink')
                os.rmdir(name, dir_fd=directory)
            finally:
                os.close(fd)
        remove(parent, path.name, expected, Path('.'))
    finally:
        os.close(parent)


def write_json(path, value):
    with Path(path).open('x') as stream:
        os.chmod(stream.name, 0o600)
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def failure_links(root, entries):
    """Archive internal links as links; external aliases retain the original."""
    links = {}
    for relative, info in entries:
        if stat.S_ISLNK(info.st_mode):
            path = root/relative
            value = os.readlink(path)
            target = Path(value) if Path(value).is_absolute() else path.parent/value
            try:
                inside = target.resolve().is_relative_to(root)
            except (OSError, RuntimeError) as exc:
                raise CleanupError('failure link cannot be resolved; retain original') from exc
            if not inside:
                raise CleanupError('failure has external aliases; retain original')
            links[relative] = value
        elif not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)) or (
                stat.S_ISREG(info.st_mode) and info.st_nlink != 1):
            raise CleanupError('failure has unsupported aliases or special files; retain original')
    return links


def verify_archive(path, root, entries, *, prefix, ignore=()):
    """Verify the whole current tree, including extra files, against saved bytes."""
    entries = [(p,s) for p,s in entries if p.as_posix() not in ignore]
    links = failure_links(root, entries)
    names = {prefix if str(p)=='.' else prefix+'/'+p.as_posix() for p,_ in entries}
    with tarfile.open(path,'r:gz') as archive:
        members = archive.getmembers()
        if len(members)!=len(names) or {m.name for m in members}!=names:
            raise CleanupError('archive inventory differs from current scratch')
        for relative, info in entries:
            name = prefix if str(relative)=='.' else prefix+'/'+relative.as_posix()
            member = archive.getmember(name)
            if member.mode != stat.S_IMODE(info.st_mode):
                raise CleanupError('archive mode differs')
            if stat.S_ISLNK(info.st_mode):
                if not member.issym() or member.linkname != links[relative]:
                    raise CleanupError('archive link differs')
            elif stat.S_ISDIR(info.st_mode):
                if not member.isdir():raise CleanupError('archive directory type differs')
            else:
                if not member.isfile():raise CleanupError('archive file type differs')
                with archive.extractfile(member) as saved, (root/relative).open('rb') as original:
                    while True:
                        block = original.read(1024*1024)
                        if saved.read(len(block)) != block:
                            raise CleanupError('archive bytes differ')
                        if not block:
                            if saved.read(1):raise CleanupError('archive file length differs')
                            break


def retained_failures(root, entries):
    found = False
    for relative,info in entries:
        if stat.S_ISREG(info.st_mode) and relative.name.startswith('.fixture-lifecycle-'):
            record = json.loads((root/relative).read_text())
            if not isinstance(record,dict) or type(record.get('retainedFailures')) is not bool:
                raise CleanupError('invalid fixture lifecycle record; retain original')
            found = found or record['retainedFailures']
    return found


def preserve_failure(root, base, expected, *, node, phases):
    """Keep failure bytes outside pytest's numbered-dir garbage collection."""
    entries = inventory(root, expected)
    if busy(root):
        raise CleanupError('failure has live users; retain original')
    links = failure_links(root, entries)
    target = private_path(base.parent/'das-fixture-failure-evidence')
    target.mkdir(mode=0o700, exist_ok=True)
    if target.stat().st_uid != os.getuid() or stat.S_IMODE(target.stat().st_mode) != 0o700:
        raise CleanupError('failure evidence destination is not private')
    if shutil.disk_usage(target).free < sum(s.st_blocks*512 for _,s in entries)+1024*1024:
        raise CleanupError('insufficient failure evidence space')
    label = uuid.uuid4().hex
    archive_path = target/(label+'.tar.gz')
    with archive_path.open('xb') as stream:
        os.chmod(archive_path,0o600)
        with tarfile.open(fileobj=stream,mode='w:gz',compresslevel=1,dereference=False) as archive:
            archive.add(root,arcname='fixture')
        stream.flush();os.fsync(stream.fileno())
    verify_archive(archive_path,root,entries,prefix='fixture')
    after = inventory(root,expected)
    snapshot = lambda rows:[(str(p),s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns) for p,s in rows]
    if snapshot(entries)!=snapshot(after) or failure_links(root,after)!=links or busy(root):
        raise CleanupError('failure changed during preservation')
    # Original modes are in the verified archive. Directory write bits make
    # later pytest collection safe, while the current failure tree stays present.
    for relative, info in entries:
        if stat.S_ISDIR(info.st_mode):
            fd = os.open(root/relative,os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                if os.fstat(fd).st_ino != info.st_ino:raise CleanupError('directory changed')
                os.fchmod(fd,stat.S_IMODE(info.st_mode)|stat.S_IRWXU)
            finally:os.close(fd)
    digest = hashlib.sha256()
    with archive_path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    receipt = {'path':str(archive_path),'sha256':digest.hexdigest(),'verifiedLocalReadback':True,
               'node':node,'phases':phases,'identity':expected,'endedAt':time.time(),
               'pytestVersion':version('pytest'),'pythonVersion':sys.version,
               'recordUse':'fixture_diagnosis_not_product_acceptance'}
    # Keep the lookup record beside the archive: pytest may collect the original
    # numbered basetemp (and its session index) in a later invocation.
    write_json(target/(label+'.json'),receipt)
    return receipt


EVIDENCE = ('*.log', '*.xml', 'runtime-attempt-*.json', 'report-attempt-*.json')


def preserve_outputs(root, destination, entries):
    records = []
    for relative, info in entries:
        if not any(fnmatch.fnmatch(relative.name, pattern) for pattern in EVIDENCE):
            continue
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > 16*1024*1024:
            raise CleanupError('unsupported evidence output')
        source = root/relative
        fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            current = os.fstat(fd)
            if (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns) != (
                    info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns):
                raise CleanupError('evidence changed')
            target = destination/relative
            private_path(target.parent)
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with target.open('xb') as output, os.fdopen(os.dup(fd), 'rb') as input_stream:
                os.chmod(target, 0o600)
                raw = input_stream.read(16*1024*1024+1)
                if len(raw) != info.st_size:
                    raise CleanupError('evidence changed')
                output.write(raw)
                output.flush()
                os.fsync(output.fileno())
            records.append({'path':relative.as_posix(), 'sha256':hashlib.sha256(raw).hexdigest(),
                            'mode':stat.S_IMODE(info.st_mode), 'bytes':len(raw)})
        finally:
            os.close(fd)
    return records


class FixtureCleanup:
    def __init__(self, *, incremental=False):
        self.roots = {}
        self.reports = {}
        self.nested = False
        self.incremental = incremental
        self.disposed = {}
        self.config = None
        self.base = None
        self.finished = False

    def configure(self, config):
        if self.config is not None and self.config is not config:
            self.__init__(incremental=self.incremental)
        self.config = config
        if config.getini('tmp_path_retention_policy') != 'all':
            raise CleanupError('DAS fixture cleanup requires tmp_path_retention_policy=all')
        existing = getattr(config, '_das_fixture_cleanup', None)
        if existing is not None:
            existing.incremental = existing.incremental or self.incremental
            return existing
        config._das_fixture_cleanup = self
        if not hasattr(config, '_das_fixture_nested'):
            config._das_fixture_nested = os.environ.get('DAS_FIXTURE_CLEANUP_PARENT') == '1'
        self.nested = config._das_fixture_nested
        os.environ['DAS_FIXTURE_CLEANUP_PARENT'] = '1'
        return self

    def register(self, node, path, base):
        self.base = Path(base)
        self.roots[node.nodeid] = (Path(path), identity(path))

    def observe(self, report):
        self.reports.setdefault(report.nodeid, {})[report.when] = report.passed
        if (self.incremental and report.when == 'teardown' and report.nodeid in self.roots
                and report.nodeid not in self.disposed):
            phases = self.reports[report.nodeid]
            if all(phases.get(p) is True for p in ('setup','call','teardown')):
                root, expected = self.roots[report.nodeid]
                base = self.base
                self.disposed[report.nodeid] = self.dispose_passed(report.nodeid,root,expected,base)

    def dispose_passed(self,node,root,expected,base):
        outcome={'node':node,'path':root.name,'phases':self.reports[node],'status':'retained'}
        try:
            entries=inventory(root,expected)
            if retained_failures(root,entries):
                outcome['reason']='nested failure evidence'
            else:
                target=base/'fixture-evidence'/hashlib.sha256(node.encode()).hexdigest()[:20]
                outcome['evidence']=preserve_outputs(root,target,entries)
                remove_owned_tree(root,expected)
                outcome['status']='removed'
        except (OSError,ValueError) as exc:
            outcome.update(status='cleanup_failed',reason=str(exc))
        return outcome

    def finish(self, session):
        if self.finished:
            return
        self.finished = True
        if not self.roots:
            return
        base = self.base
        results = []
        for node, (root, expected) in self.roots.items():
            phases = self.reports.get(node, {})
            passed = all(phases.get(phase) is True for phase in ('setup','call','teardown'))
            if node in self.disposed:
                outcome=self.disposed[node]
            else:
                outcome = {'node':node, 'path':root.name, 'phases':phases, 'status':'retained'}
                if passed and not self.nested:
                    outcome=self.dispose_passed(node,root,expected,base)
            if not self.nested and (not passed or outcome.get('reason')=='nested failure evidence'):
                try:
                    outcome['failureArchive'] = preserve_failure(root,base,expected,node=node,phases=phases)
                except (OSError,ValueError,tarfile.TarError) as exc:
                    outcome['archiveError'] = str(exc)
                    outcome.setdefault('reason',str(exc))
            if outcome['status']=='cleanup_failed':session.exitstatus=1
            results.append(outcome)
        label = hashlib.sha256(str(Path(__file__).absolute()).encode()).hexdigest()[:16]
        write_json(base/('.fixture-lifecycle-'+label+'.json'), {
            'nested':self.nested, 'retainedFailures':any(
                not all(item['phases'].get(phase) is True for phase in ('setup','call','teardown')) or
                item.get('reason')=='nested failure evidence' or item['status']=='cleanup_failed'
                for item in results), 'roots':results})
