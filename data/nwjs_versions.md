# nw.js versions used by the game

## nw.js update history

### Windows 32-bit

| game version | nw.js version      | notes            | blog post link  |
| ------------ | ------------------ | ---------------- | --------------- |
| 0.1.6        | [0.8.3][nw0.8.3]   | first release    | [link][rfg3574] |
| 0.9.8-8      | [0.30.5][nw0.30.5] | upgraded         | [link][rfg6380] |
| 1.0.0-1      | [0.8.3][nw0.8.3]   | downgraded       |                 |
| 1.0.0-7      | [0.30.5][nw0.30.5] | upgraded back    | [link][rfg6468] |
| 1.0.0-10     | [0.8.3][nw0.8.3]   | downgraded again |                 |
| 1.0.1        | [0.30.5][nw0.30.5] | finally upgraded | [link][rfg6493] |
| 1.2.0-5      | [0.35.5][nw0.35.5] | upgraded         | [link][rfg6904] |

The `nwjs_old` branch has always been on [0.8.3][nw0.8.3].

The `nwjs_new` branch has always been on [0.30.5][nw0.30.5].

### Windows 64-bit

| game version | nw.js version             | notes                            | blog post link  |
| ------------ | ------------------------- | -------------------------------- | --------------- |
| 1.0.0-7      | [0.30.5][nw0.30.5]        | first 64-bit release for Windows | [link][rfg6468] |
| 1.0.0-10     | [0.8.3][nw0.8.3] (32-bit) | downgraded                       |                 |
| 1.0.1        | [0.30.5][nw0.30.5]        | upgraded                         | [link][rfg6493] |
| 1.2.0-5      | [0.35.5][nw0.35.5]        | upgraded                         | [link][rfg6904] |

The `nwjs_old` branch has always been on [0.8.3][nw0.8.3] (32-bit).

The `nwjs_new` branch has always been on [0.30.5][nw0.30.5].

### Linux 64-bit and 32-bit

| game version | nw.js version            | notes                      | blog post link  |
| ------------ | ------------------------ | -------------------------- | --------------- |
| 0.5.0        | [0.12.1][nw0.12.1]       | first release for Linux    | [link][rfg4274] |
| 0.7.0        | [0.14.5][nw0.14.5]       | upgraded                   | [link][rfg4759] |
| 0.9.8        | [0.14.5][nw0.14.5] (SDK) | switched to the SDK flavor | [link][rfg5953] |
| 0.9.8-8      | [0.30.5][nw0.30.5]       | upgraded                   | [link][rfg6380] |
| 1.0.0-1      | [0.14.5][nw0.14.5]       | downgraded                 |                 |
| 1.0.1        | [0.30.5][nw0.30.5]       | upgraded back              | [link][rfg6493] |
| 1.2.0-5      | [0.35.5][nw0.35.5]       | upgraded                   | [link][rfg6904] |
| 1.4.2-2      | [0.63.1][nw0.63.1]       | upgraded                   |                 |

The `nwjs_old` branch has always been on [0.14.5][nw0.14.5].

The `nwjs_new` branch has always been on [0.30.5][nw0.30.5].

### macOS

| game version | nw.js version               | notes                           | blog post link  |
| ------------ | --------------------------- | ------------------------------- | --------------- |
| 0.5.0        | [0.12.1][nw0.12.1] (32-bit) | first release for macOS         | [link][rfg4274] |
| 0.7.0        | [0.14.5][nw0.14.5]          | upgraded and switched to 64-bit | [link][rfg4759] |
| 0.9.8        | [0.14.5][nw0.14.5] (SDK)    | switched to the SDK flavor      | [link][rfg5953] |
| 0.9.8-8      | [0.30.5][nw0.30.5]          | upgraded                        | [link][rfg6380] |
| 1.0.0-1      | [0.14.5][nw0.14.5]          | downgraded                      |                 |
| 1.0.1        | [0.30.5][nw0.30.5]          | upgraded back                   | [link][rfg6493] |
| 1.2.0-5      | [0.35.5][nw0.35.5]          | upgraded                        | [link][rfg6904] |
| 1.4.0        | [0.50.3][nw0.50.3]          | upgraded yet again              | [link][rfg7071] |

The `nwjs_old` branch has always been on [0.14.5][nw0.14.5].

The `nwjs_new` branch has always been on [0.30.5][nw0.30.5].

## nw.js metadata

### v0.8.3

[Download page][nw0.8.3]

```json
{
  "http_parser": "1.0",
  "node": "0.10.22",
  "v8": "3.20.15.5",
  "ares": "1.9.0-DEV",
  "uv": "0.10.19",
  "zlib": "1.2.5",
  "modules": "11",
  "openssl": "1.0.1e",
  "node-webkit": "0.8.3",
  "chromium": "30.0.1599.66"
}
```

### v0.12.1

[Download page][nw0.12.1]

```json
{
  "http_parser": "2.3.0",
  "node": "1.2.0",
  "v8": "3.32.7",
  "uv": "1.4.0",
  "zlib": "1.2.5",
  "ares": "1.10.0-DEV",
  "modules": "43",
  "openssl": "1.0.1k",
  "node-webkit": "0.12.1",
  "nw-commit-id": "51300af-0aa4273-be948af-459755a-2bdc251-1764a45",
  "chromium": "41.0.2272.76"
}
```

### v0.14.5

[Download page][nw0.14.5]

```json
{
  "http_parser": "2.7.0",
  "node": "5.11.1",
  "v8": "5.0.71.48",
  "uv": "1.8.0",
  "zlib": "1.2.5",
  "ares": "1.10.1-DEV",
  "icu": "54.1",
  "modules": "47",
  "openssl": "1.0.2h",
  "nw": "0.14.5",
  "node-webkit": "0.14.5",
  "nw-commit-id": "93c8021-3478215-2a9e6e1-5a26102",
  "chromium": "50.0.2661.102"
}
```

### v0.30.5

[Download page][nw0.30.5]

```json
{
  "http_parser": "2.8.0",
  "node": "10.1.0",
  "v8": "6.6.346.32",
  "uv": "1.20.2",
  "zlib": "1.2.11",
  "ares": "1.14.0",
  "modules": "64",
  "nghttp2": "1.29.0",
  "napi": "3",
  "openssl": "1.1.0h",
  "icu": "60.1",
  "unicode": "10.0",
  "cldr": "32.0",
  "tz": "2018c",
  "nw": "0.30.5",
  "node-webkit": "0.30.5",
  "nw-commit-id": "29d01bf-33cd709-b58e580-00b3abb",
  "nw-flavor": "normal",
  "chromium": "66.0.3359.181"
}
```

### v0.35.5

[Download page][nw0.35.5]

```json
{
  "node": "11.6.0",
  "v8": "7.1.302.31",
  "uv": "1.24.1",
  "zlib": "1.2.11",
  "ares": "1.15.0",
  "modules": "67",
  "nghttp2": "1.34.0",
  "napi": "3",
  "llhttp": "1.0.1",
  "http_parser": "2.8.0",
  "openssl": "1.1.0j",
  "icu": "62.1",
  "unicode": "11.0",
  "cldr": "33.1",
  "tz": "2018g",
  "nw": "0.35.5",
  "node-webkit": "0.35.5",
  "nw-commit-id": "d407606-fea7e3a-be1160e-f4acdc0",
  "nw-flavor": "sdk",
  "chromium": "71.0.3578.98"
}
```

### v0.50.3

[Download page][nw0.50.3]

```json
{
  "node": "15.5.1",
  "v8": "8.7.220.31",
  "uv": "1.40.0",
  "zlib": "1.2.11",
  "brotli": "1.0.9",
  "ares": "1.17.1",
  "modules": "88",
  "nghttp2": "1.41.0",
  "napi": "7",
  "llhttp": "2.1.3",
  "openssl": "1.1.1i",
  "icu": "67.1",
  "unicode": "13.0",
  "nw": "0.50.3",
  "node-webkit": "0.50.3",
  "nw-commit-id": "0789755-0ffab9c-050bd3e-49b68d6",
  "nw-flavor": "sdk",
  "chromium": "87.0.4280.141"
}
```

### v0.63.1

[Download page][nw0.63.1]

```json
{
  "node": "17.8.0",
  "v8": "10.0.139.15",
  "uv": "1.43.0",
  "zlib": "1.2.11",
  "brotli": "1.0.9",
  "ares": "1.18.1",
  "modules": "102",
  "nghttp2": "1.47.0",
  "napi": "8",
  "llhttp": "6.0.4",
  "openssl": "3.0.2+quic",
  "icu": "70.1",
  "unicode": "14.0",
  "nw": "0.63.1",
  "node-webkit": "0.63.1",
  "nw-commit-id": "db6c6a7-29d2f39-e46a141-39a2416",
  "nw-flavor": "normal",
  "chromium": "100.0.4896.127"
}
```

[rfg3574]: http://www.radicalfishgames.com/?p=3574
[rfg4274]: http://www.radicalfishgames.com/?p=4274
[rfg4759]: http://www.radicalfishgames.com/?p=4759
[rfg5953]: http://www.radicalfishgames.com/?p=5953
[rfg6380]: http://www.radicalfishgames.com/?p=6380
[rfg6468]: http://www.radicalfishgames.com/?p=6468
[rfg6493]: http://www.radicalfishgames.com/?p=6493
[rfg6904]: http://www.radicalfishgames.com/?p=6904
[rfg7071]: http://www.radicalfishgames.com/?p=7071
[nw0.8.3]: https://dl.nwjs.io/v0.8.3/
[nw0.12.1]: https://dl.nwjs.io/v0.12.1/
[nw0.14.5]: https://dl.nwjs.io/v0.14.5/
[nw0.30.5]: https://dl.nwjs.io/v0.30.5/
[nw0.35.5]: https://dl.nwjs.io/v0.35.5/
[nw0.50.3]: https://dl.nwjs.io/v0.50.3/
[nw0.63.1]: https://dl.nwjs.io/v0.63.1/
