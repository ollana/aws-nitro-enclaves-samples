#!/usr/local/bin/env python3

# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import argparse
import socket
import sys
import os
import requests
import json




class VsockStream:
    """Client"""
    def __init__(self, conn_tmo=5):
        self.conn_tmo = conn_tmo

    def connect(self, endpoint):
        """Connect to the remote endpoint"""
        self.sock = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
        self.sock.settimeout(self.conn_tmo)
        self.sock.connect(endpoint)

    def send_data(self, data):
        """Send data to the remote endpoint"""
        self.sock.sendall(data)
        rec_data=self.sock.recv(1024).decode()
        print('received: ', rec_data)
        self.sock.close()


def client_handler(args):
    client = VsockStream()
    endpoint = (args.cid, args.port)
    client.connect(endpoint)
    msg = args.msg
    credentials = fetch_aws_credentials()
    req = {
        'cipher': msg,
        'kms_credentials': credentials

    }
    client.send_data(str.encode(json.dumps(req)))


class VsockListener:
    """Server"""
    def __init__(self, conn_backlog=128):
        self.conn_backlog = conn_backlog

    def bind(self, port):
        """Bind and listen for connections on the specified port"""
        self.sock = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
        self.sock.bind((socket.VMADDR_CID_ANY, port))
        self.sock.listen(self.conn_backlog)

    def recv_data(self):
        """Receive data from a remote endpoint"""
        while True:
            (from_client, (remote_cid, remote_port)) = self.sock.accept()
            data = from_client.recv(1024).decode()
            if not data:
                break
            print("cipher received:"+data)


            stream = os.popen('echo $(aws kms decrypt --ciphertext-blob ' + data + ' --query Plaintext --output text)')
            output = stream.read()

            print("decrypted: "+output)

            from_client.sendall(output.encode())
            from_client.close()


def server_handler(args):
    server = VsockListener()
    server.bind(args.port)
    server.recv_data()


def main():
    parser = argparse.ArgumentParser(prog='vsock-sample')
    parser.add_argument("--version", action="version",
                        help="Prints version information.",
                        version='%(prog)s 0.1.0')
    subparsers = parser.add_subparsers(title="options")

    client_parser = subparsers.add_parser("client", description="Client",
                                          help="Connect to a given cid and port.")
    client_parser.add_argument("cid", type=int, help="The remote endpoint CID.")
    client_parser.add_argument("port", type=int, help="The remote endpoint port.")
    client_parser.add_argument("msg", help="The cipher to decrypt.")
    client_parser.set_defaults(func=client_handler)

    server_parser = subparsers.add_parser("server", description="Server",
                                          help="Listen on a given port.")
    server_parser.add_argument("port", type=int, help="The local port to listen on.")
    server_parser.set_defaults(func=server_handler)

    if len(sys.argv) < 2:
        parser.print_usage()
        sys.exit(1)

    args = parser.parse_args()
    args.func(args)


def fetch_aws_credentials():
    """Fetch the AWS session token from the metadata service."""
    instance_profile_response = requests.get(
        'http://169.254.169.254/latest/meta-data/iam/security-credentials/'
    )
    instance_profile_name = instance_profile_response.text

    sec_credentials_response = requests.get(
        f'http://169.254.169.254/latest/meta-data/iam/security-credentials/{instance_profile_name}'
    )
    response = sec_credentials_response.json()

    return {
        'aws_access_key_id' : response['AccessKeyId'],
        'aws_secret_access_key' : response['SecretAccessKey'],
        'aws_session_token' : response['Token']
    }

if __name__ == "__main__":
    main()
