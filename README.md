## Nitro Enclaves Samples

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.

Eclave usage example (based on https://docs.aws.amazon.com/enclaves/latest/user/vsock.html

Inside the parent instance:
```
git clone https://github.com/ollana/aws-nitro-enclaves-samples.git
```
```
cd aws-nitro-enclaves-samples
```
```
vi Dockerfile 
```
```
# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

FROM python:3.7.9-alpine3.12

COPY vsock_sample/py/vsock-sample.py .

CMD ["/usr/local/bin/python3", "vsock-sample.py", "server", "5005"]
```
```
nitro-cli build-enclave --docker-dir ./ --docker-uri vsock-sample-server --output-file vsock_sample.eif
```
```
nitro-cli run-enclave --eif-path vsock_sample.eif --cpu-count 2 --enclave-cid 6 --memory 256 --debug-mode
```
```
nitro-cli console --enclave-id enclave_id
```
Open an SSh terminal window for the parent instanse and run:
```
cd aws-nitro-enclaves-samples/vsock_sample/py
```
```
python3 vsock-sample.py client 6 5005
```



