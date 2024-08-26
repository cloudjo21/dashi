
### deployment configuration directory for api servers

#### format

```shell
$NAUTS_LOCAL_ROOT/user/[username]/[host_or_container_name]/[snapshot_dt]/deploys/
```

#### example

```shell
$HOME/temp/user/[username]/[hostname]/220502_000000_000000/deploys/
```

##### config file for model below deployment configuration directory

```shell
model/model_deploy.json
```

##### config file for pretrained language model below deployment configuration directory

```shell
pretrained_model/pretrained_model_deploy.json
```

##### config file for pretrained language model below deployment configuration directory

```shell
vector/vector_deploy.json
```
