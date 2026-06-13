# Memory Pollution Dose-Response (LLM Agents)

Controlled fabricated-memory evidence (fake risk violations, fake
rejections) is injected into the agent's recalled risk feedback; the
risk gate keeps reading the raw journal. Outcomes are behavioral
(hold ratio, turnover) since the deterministic overlay's amplification
metric does not apply to LLM decisions. Paired within seed, samples
averaged, BH-FDR over the model x kind x dose family.

Agents: deepseek:deepseek-v4-pro, glm:glm-5, poe:claude-opus-4.7, poe:gemini-3.1-pro, poe:glm-5, poe:gpt-5.5.

## Highest-dose hold-ratio shift (conservatism under fabricated risk)

| Agent | Kind | Hold-ratio delta | Cohen's d | perm p |
| --- | --- | ---: | ---: | ---: |
| deepseek:deepseek-v4-pro | fake_rejections | +0.079 | 0.79 | 0.008 |
| deepseek:deepseek-v4-pro | fake_violations | +0.125 | 0.69 | 0.051 |
| glm:glm-5 | fake_rejections | -0.012 | -0.62 | 0.125 |
| glm:glm-5 | fake_violations | +0.013 | 0.46 | 0.250 |
| poe:claude-opus-4.7 | fake_rejections | -0.006 | -0.47 | 0.500 |
| poe:claude-opus-4.7 | fake_violations | -0.001 | -0.14 | 1.000 |
| poe:gemini-3.1-pro | fake_rejections | +0.042 | 0.47 | 0.195 |
| poe:gemini-3.1-pro | fake_violations | +0.081 | 1.22 | 0.010 |
| poe:glm-5 | fake_rejections | -0.006 | -0.18 | 0.672 |
| poe:glm-5 | fake_violations | +0.015 | 0.45 | 0.344 |
| poe:gpt-5.5 | fake_rejections | +0.000 | 0.00 | 1.000 |
| poe:gpt-5.5 | fake_violations | -0.001 | -0.32 | 1.000 |

## Significant dose effects (BH-FDR q<0.05)

| Agent | Kind | Risk | Dose | Outcome | Delta | q |
| --- | --- | --- | ---: | --- | ---: | ---: |
