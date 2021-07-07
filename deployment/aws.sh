#!/usr/bin/env bash

ansible-playbook -u ubuntu -i hosts/aws aws.yml "$@"
