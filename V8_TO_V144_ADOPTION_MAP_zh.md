# V8 → V1.4.4 采纳映射

> **状态**: Active  
> **治理标准**: DAS v1.4.6  
> **适用范围**: 从 DAS v0.8 或更早版本迁移到 v1.4.4+ 的仓库

## 概述

本文档为从 DAS v0.8（或旧版未版本化基线）迁移到 v1.4.4+ 的团队提供采纳映射和检查清单。

## 迁移检查清单

### 阶段 1：结构对齐

| 检查项 | 旧版 (v0.8) | 新版 (v1.4.4+) | 操作 |
|--------|-------------|----------------|------|
| 标准清单 | 无 | `standard_manifest.json` | 运行 `dasops adopt` 生成 |
| 版本闭包 | 手动跟踪 | `suite_version_closure.json` | 从 `das-suite` 同步 |
| 工具锁定 | 无 | `tooling_lock.json` | 运行 `dasops create` 生成模板 |
| 本地扩展 | 内联声明 | `local_extension_manifest.json` | 迁移到 schema 格式 |

### 阶段 2：文档对齐

| 检查项 | 操作 |
|--------|------|
| Master Doc 元数据 | 添加 `Doc family role`, `Conformance profile` 等必填字段 |
| 合同清单索引 | 添加 `Contract inventory index` 章节 |
| 追踪索引 | 添加 `Traceability index` 章节 |
| AI 执行计划 | 添加 `AI Execution Plan` 章节 |

### 阶段 3：验证对齐

| 检查项 | 操作 |
|--------|------|
| verify 脚本 | 确保 `scripts/verify` 存在并执行所有门控 |
| CI 工作流 | 添加 `.github/workflows/verify.yml` |
| 发布工作流 | 添加 `.github/workflows/release.yml` |

## 工具支持

```bash
# 评估当前仓库状态
dasops doctor

# 采纳现有仓库
dasops adopt --standard-version 1.4.6

# 验证迁移完整性
scripts/verify
```

## 常见问题

**Q: 是否必须一次性迁移所有内容？**  
A: 不需要。可以分阶段采纳——结构对齐 → 文档对齐 → 验证对齐。`dasops doctor` 会报告当前进度。

**Q: 旧版扩展声明如何处理？**  
A: 迁移到 `local_extension_manifest.json` 格式，使用 `dasops adopt` 自动检测并生成初始清单。
