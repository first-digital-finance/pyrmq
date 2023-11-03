## [3.4.4](https://github.com/first-digital-finance/pyrmq/compare/v3.4.3...v3.4.4) (2023-11-03)


### Bug Fixes

* **pyrmq.consumer:** fix heartbeat kwargs conflict with pika ([a11e7ce](https://github.com/first-digital-finance/pyrmq/commit/a11e7cefb7890dd33b1970606fd11aa3e7eed7b0))

## [3.4.3](https://github.com/first-digital-finance/pyrmq/compare/v3.4.2...v3.4.3) (2023-11-03)


### Bug Fixes

* **pyrmq.consumer:** add heartbeat kwargs for pika heartbeat config ([317c8ee](https://github.com/first-digital-finance/pyrmq/commit/317c8ee0f2936d9216506c21068ff3c75e4ae2b1))

## [3.4.2](https://github.com/first-digital-finance/pyrmq/compare/v3.4.1...v3.4.2) (2022-09-15)


### Bug Fixes

* **consumer:** use the correct kwarg for retry_interval ([a613310](https://github.com/first-digital-finance/pyrmq/commit/a613310d79ec23dd64312779233b23bf6ec64732))

## [3.4.1](https://github.com/first-digital-finance/pyrmq/compare/v3.4.0...v3.4.1) (2021-12-02)


### Bug Fixes

* add more exceptions to retry during connection attempts ([fa9e19e](https://github.com/first-digital-finance/pyrmq/commit/fa9e19ee645235ef92ab160f1fe9c3a71f2eeeb3))

# [3.4.0](https://github.com/first-digital-finance/pyrmq/compare/v3.3.0...v3.4.0) (2021-10-29)


### Features

* add Python 3.10 support ([4f36653](https://github.com/first-digital-finance/pyrmq/commit/4f366530b58d0150de13f19cb93ed95f56e23cca))

# [3.3.0](https://github.com/first-digital-finance/pyrmq/compare/v3.2.0...v3.3.0) (2021-08-25)


### Features

* **dlk:** use periodic retry instead of retry backoff for DLX-DLK logic ([5a34c0d](https://github.com/first-digital-finance/pyrmq/commit/5a34c0d12134f759ee20f434b2324a0d44e5168d))

# [3.2.0](https://github.com/first-digital-finance/pyrmq/compare/v3.1.0...v3.2.0) (2021-03-16)


### Features

* **consumer:** add prefetch_count kwarg ([3c814cb](https://github.com/first-digital-finance/pyrmq/commit/3c814cbbc39b6306104bc6eb289ff7479af65148))

# [3.1.0](https://github.com/first-digital-finance/pyrmq/compare/v3.0.0...v3.1.0) (2021-03-03)


### Features

* **consumer:** allow for consumers use bound exchanges ([988dd90](https://github.com/first-digital-finance/pyrmq/commit/988dd90afa49175e861e656025912a5d2b99a655))

# [3.0.0](https://github.com/first-digital-finance/pyrmq/compare/v2.1.1...v3.0.0) (2021-03-03)


### Bug Fixes

* add exchange_args to both consumer and publisher ([#36](https://github.com/first-digital-finance/pyrmq/issues/36)) ([e5799a0](https://github.com/first-digital-finance/pyrmq/commit/e5799a0c98527629b39726f4518fc6458d031059))
* pass error and error_type to error_callback ([afc56da](https://github.com/first-digital-finance/pyrmq/commit/afc56da035edf545678bf9acfb1e0cb7abd1d9d0))


### BREAKING CHANGES

* error_callback should accept additional keyword
arguments namely `error` and `error_type`

## [2.1.1](https://github.com/first-digital-finance/pyrmq/compare/v2.1.0...v2.1.1) (2021-02-16)


### Bug Fixes

* log an exception only if error_callback field is not initialized ([#35](https://github.com/first-digital-finance/pyrmq/issues/35)) ([b2bebd7](https://github.com/first-digital-finance/pyrmq/commit/b2bebd7f3a868996cd1adcd11d701319c417b4c8))

# [2.1.0](https://github.com/first-digital-finance/pyrmq/compare/v2.0.0...v2.1.0) (2021-02-01)


### Features

* **consumer:** add a new option ([387d1e8](https://github.com/first-digital-finance/pyrmq/commit/387d1e8de25b64db020d6c1adc8d7a4a41c9e539))

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
