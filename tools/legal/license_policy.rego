package das.license

default allow = false

allowed_licenses := {
  "Apache-2.0",
  "BSD-2-Clause",
  "BSD-3-Clause",
  "CC0-1.0",
  "ISC",
  "MIT",
  "PSF-2.0",
}

denied_licenses := {
  "AGPL-3.0-only",
  "GPL-2.0-only",
  "GPL-3.0-only",
  "LGPL-3.0-only",
}

review_licenses := {
  "EPL-2.0",
  "MPL-2.0",
}

allow {
  allowed_licenses[input.license]
}

deny[msg] {
  denied_licenses[input.license]
  msg := sprintf("%s is denied for commercial redistribution", [input.license])
}

deny[msg] {
  not input.license
  msg := "license is missing"
}

review[msg] {
  review_licenses[input.license]
  msg := sprintf("%s requires legal review", [input.license])
}
