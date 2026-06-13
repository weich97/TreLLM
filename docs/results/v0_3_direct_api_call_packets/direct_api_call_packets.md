# TreLLM v0.3 Direct API Call Packets

This artifact turns the pre-registered direct API matrix plan into hash-bound call packets.
It does not make provider calls and does not publish raw prompts or raw responses.

- Protocol: `trellm-v0.3-iclr-protocol`
- Source plan rows: `docs/results/v0_3_direct_api_matrix_plan/direct_api_matrix_plan_rows.csv`
- Call packets: `30`
- Credential-ready packets: `0`
- Not-run packets: `30`
- Claim boundary: Call packets make the pre-registered direct API matrix executable and auditable. They do not call providers, store raw prompts, store raw responses, or support model-performance claims.

## Manifest

| Provider | Model | Scenario | Seed | Sample | Credential ready | Prompt packet hash | Status | Blocking reasons |
| --- | --- | --- | ---: | ---: | --- | --- | --- | --- |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 7 | 0 | false | `sha256:8f534f986151114e6ccdc00798521f90a4c931f7463a8ae441f8aa7341ba8843` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 7 | 1 | false | `sha256:badb3dcd3bc704f7822df8c0c9ad414bfc2908fe08e58dfa1b2f874d347edafc` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 7 | 2 | false | `sha256:4796fe8ab00d4fda7019aa757cce05d87328d0e19214eb2ed862b6dd869dd567` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 11 | 0 | false | `sha256:7747f0d297d40c316f053e5071d604146b0b60963910c9c1182482b0cd966d36` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 11 | 1 | false | `sha256:337bd822aee439d4590d48abc648fc251fea6345511e4c1b135dc7104743f19a` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 11 | 2 | false | `sha256:f6db2b865da8392f9d9320f4df91a7db7dd5a9dd0f6127200132ef5db1c92144` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 17 | 0 | false | `sha256:d22c39c3cb99bff2713e8e6b4bed585d82a27de63862e1aed733d0c3dd7c6cf5` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 17 | 1 | false | `sha256:d5585c745c4e353acca1daefdce9205514f2f540e7bed27452973f4d90a69926` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 17 | 2 | false | `sha256:12fdb9005cc4f1e884181e24c276271aa546088dc6259430d772e26f8e4c22c8` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 23 | 0 | false | `sha256:6c08973bab9d1d5cbc39c58b4c45fcbd2ca1682aa00728717e7b62054137c97c` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 23 | 1 | false | `sha256:99f98ebb6c16c5d81ed4530006038f18e327538adf8a535afb02d04800979fd2` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 23 | 2 | false | `sha256:4ab89d8f0523e5d39d4c87b46ced758d62197bcfb78580461ce9e5778e8bee33` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 31 | 0 | false | `sha256:3dbf9d2765ed5cad164804794dafc4279c9610c99ebdb1332319726183ce3050` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 31 | 1 | false | `sha256:0607cb53e17b944309f5100bdde4198429cf9c96bb0c5f33c4c5ebb4cf11fc9b` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 31 | 2 | false | `sha256:bb8300f19db6e0601396d63df698d0ec4d9ce6e7c841b67e65121c954c66b598` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 37 | 0 | false | `sha256:08a786b38a859b9f2dd6c14de4c6c90a0735cc879b168e6ccd6ceeba9e2956df` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 37 | 1 | false | `sha256:7197a27000faba9e4872c764ee535b1d9a6d7241fd927382f1e741684127b295` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 37 | 2 | false | `sha256:af00f94fb3d6d21a02398c125f8886071531ab33b6c7c16090d2162f80e02266` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 41 | 0 | false | `sha256:92c94f9cd979d4a6f4187dc431d14237e1d771d44cb62a631c72fae61613370e` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 41 | 1 | false | `sha256:4e5c193fbf2fa7ec59ad64b9a12ee7259b3875d433464cc0aa0e80632df0d37b` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 41 | 2 | false | `sha256:f1343361f0d9661d2598db5d58888ed201ba8206edca5306f9fceab8fa9ffbb6` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 43 | 0 | false | `sha256:169ded001299674c23f45790413c5b6abe2ef23df38bc3ee8e8a1a32cb38bcfc` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 43 | 1 | false | `sha256:aa942e0218f03fbf344d891e4df417b7e587edc279d47abe31d35460d30d3061` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 43 | 2 | false | `sha256:cfa4aa9f1cc3b1014c7a3e4f1c85238d803a3900cf5a48122b4714b19dbfa997` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 47 | 0 | false | `sha256:f3e7b7efb63f830b47e989840ee3aa2f26dd8161e538a64757513598d42d3130` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 47 | 1 | false | `sha256:d883ae7959526dc2d4b7c5b543dc6b34f5400a4494fabc528601f67bf8dcc0bc` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 47 | 2 | false | `sha256:0d208a2b9e4dd479221940fca854b9802a9361aeb33514e6ae7bf86f57d6ab5f` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 53 | 0 | false | `sha256:94c15dd41d3d986a6f81b8802c3ceea9e73875c7d6342387d7dee6e1c68ad698` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 53 | 1 | false | `sha256:0d9343d6455b8d1b3936dc02be0675c5f2f90f3cb535f71b35923f0fa57ba847` | not_run | credential_env_var_missing |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | 53 | 2 | false | `sha256:d6bad7551ca2b4e3f7a1fce1d7885a80fc9193723cf6ae08bef4e57b0b410d0b` | not_run | credential_env_var_missing |
