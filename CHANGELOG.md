# [2.0.0](https://github.com/first-digital-finance/pyrmq/compare/v1.5.3...v2.0.0) (2021-01-18)


### Features

* **consumer:** add channel, method, and properties to the specified callback as kwargs ([7252421](https://github.com/first-digital-finance/pyrmq/commit/72524218ccb61ab7f1f02ed949690d10a4cbed77))


### BREAKING CHANGES

* **consumer:** specified Consumer callback methods should accept
`channel`, `method`, and `properties` as additional keyword arguments

## [1.5.3](https://github.com/first-digital-finance/pyrmq/compare/v1.5.2...v1.5.3) (2020-12-11)


### Bug Fixes

* **consumer:** allow the consumer to specify its exchange type ([1b7a5b6](https://github.com/first-digital-finance/pyrmq/commit/1b7a5b683e10438a174204b7d28792e7f4c36c7f))

## [1.5.2](https://github.com/first-digital-finance/pyrmq/compare/v1.5.1...v1.5.2) (2020-12-11)


### Bug Fixes

* **consumer:** input correct credentials for connecting ([1e99cbb](https://github.com/first-digital-finance/pyrmq/commit/1e99cbba9928559cd2c07c41625f29311bfa16ab))

## [1.5.1](https://github.com/first-digital-finance/pyrmq/compare/v1.5.0...v1.5.1) (2020-12-04)


### Bug Fixes

* relax setup.py package requirements ([615e87f](https://github.com/first-digital-finance/pyrmq/commit/615e87fc99660ad86e5e8494f6ebeb9255b84615))

# [1.5.0](https://github.com/first-digital-finance/pyrmq/compare/v1.4.0...v1.5.0) (2020-12-04)


### Features

* **consumer:** Consumer class now declares queues ([67e1bf7](https://github.com/first-digital-finance/pyrmq/commit/67e1bf7772eb1e94d60a028bf3e42b1e57ad7c7f))
* add support for Python 3.9 ([09a884c](https://github.com/first-digital-finance/pyrmq/commit/09a884c0a84effeaa314ec4fb152b789a5936b14))

# [1.4.0](https://github.com/first-digital-finance/pyrmq/compare/v1.3.0...v1.4.0) (2020-12-03)


### Features

* allow different exchange types ([c6df4e0](https://github.com/first-digital-finance/pyrmq/commit/c6df4e0210133b22eab0054f44f089d5c5da2c38))

# [1.3.0](https://github.com/first-digital-finance/pyrmq/compare/v1.2.0...v1.3.0) (2020-11-26)


### Features

* implement dead-letter queue retry logic ([f1ccdf7](https://github.com/first-digital-finance/pyrmq/commit/f1ccdf794f7bb97e433d5f3d1ba2bfbe3773068c))

# [1.2.0](https://github.com/first-digital-finance/pyrmq/compare/v1.1.0...v1.2.0) (2020-11-05)


### Features

* implement message priorities ([ae93321](https://github.com/first-digital-finance/pyrmq/commit/ae9332120f96164f5006d8c446f157ba30575ba1))
