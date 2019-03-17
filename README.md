# qcloud_cns
tencent cloud cns record

## config.yaml
You need to change: 
```yaml
---
secretID:
secretKey:
default_domain: 
```
in config.yaml

## Usage:
Please copy config.yaml.template to config.yaml and modify it.
```bash
echo $subDomain $value | python qcloud.py -d $domain
```
