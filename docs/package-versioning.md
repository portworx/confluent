---
post_title: Package Versioning
menu_order: 80
post_excerpt: ""
feature_maturity: preview
enterprise: 'no'
---

Packages are versioned with an `a.b.c-x.y.z` format, where `a.b.c` is the version of the service management layer and `x.y.z` indicates the version of Confluent Kafka. For example, `1.1.20-3.2.0` indicates version `1.1.20` of the service management layer and version `3.2.0` of Confluent Kafka.

### Upgrades/downgrades

The package supports upgrade and rollback between adjacent versions only. For example, to upgrade from version 2 to version 4, you must first complete an upgrade to version 3, followed by an upgrade to version 4.
