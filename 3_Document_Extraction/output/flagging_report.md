# Flagging Report

Confidence threshold: **0.75**

Documents processed: 10
Documents flagged for human review: 3

## Flagged items

### 04_passport.png -> `passport`
- Reason: 1 field(s) below confidence threshold
  - **mrz_line_2**: value=`X1234567<7IND7912185M3001010<<<<<<<<<<<<<<<<<<<08`, confidence=0.4, reason=Value 'X1234567<7IND7912185M3001010<<<<<<<<<<<<<<<<<<<08' does not match expected format for mrz_line_2

### 06_fatca_annexure.jpeg -> `fatca_annexure`
- Reason: 1 field(s) below confidence threshold
  - **tin_pan**: value=`BPQPD 3051R`, confidence=0.4, reason=Value 'BPQPD 3051R' does not match expected format for tin_pan

### 10_suitability_profiler.jpeg -> `error`
- Reason: Processing error: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. \n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 5, model: gemini-2.5-flash\nPlease retry in 17.488898814s.', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://ai.google.dev/gemini-api/docs/rate-limits'}]}, {'@type': 'type.googleapis.com/google.rpc.QuotaFailure', 'violations': [{'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerMinutePerProjectPerModel-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-2.5-flash'}, 'quotaValue': '5'}]}, {'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '17s'}]}}
