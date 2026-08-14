# OCR Evaluation Harness Summary

> **Historical/fixture-only warning:** The zero-error and zero-latency values below are archived harness output and must not be reported as production OCR accuracy. The current evaluator distinguishes native text, mock OCR, and real PaddleOCR execution; image OCR remains `NOT RUN`/`UNAVAILABLE` until a non-mock engine artifact is produced on an exact SHA.

- **Gold Pages Evaluated:** 5
- **Total Scan Variants:** 10
- **Overall CER:** 0.0000
- **Overall WER:** 0.0000
- **Overall Clinical Accuracy:** 100.00%

## Performance & Field Accuracy Breakdown by Image Variant

| Variant | Pages | CER | WER | Clinical Accuracy | Decimal Misreads | Mean Latency (s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `rot_90` | 5 | 0.0000 | 0.0000 | 100.0% | 0 | 0.000 |
| `rot_180` | 5 | 0.0000 | 0.0000 | 100.0% | 0 | 0.000 |
| `rot_270` | 5 | 0.0000 | 0.0000 | 100.0% | 0 | 0.000 |
| `low_res_72dpi` | 5 | 0.0000 | 0.0000 | 100.0% | 0 | 0.000 |
| `low_res_150dpi` | 5 | 0.0000 | 0.0000 | 100.0% | 0 | 0.000 |
| `blur_light` | 5 | 0.0000 | 0.0000 | 100.0% | 0 | 0.000 |
| `blur_heavy` | 5 | 0.0000 | 0.0000 | 100.0% | 0 | 0.000 |
| `noise_gaussian` | 5 | 0.0000 | 0.0000 | 100.0% | 0 | 0.000 |
| `contrast_low` | 5 | 0.0000 | 0.0000 | 100.0% | 0 | 0.000 |
| `skew_slight` | 5 | 0.0000 | 0.0000 | 100.0% | 0 | 0.000 |
