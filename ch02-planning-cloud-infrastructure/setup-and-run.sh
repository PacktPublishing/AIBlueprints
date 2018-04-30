#!/bin/sh

instancetype=$1
machineid=$2
shift; shift
taskids=$*

aws ec2 run-instances --image-id ami-3179bd4c --count 1 \
    --instance-type $instancetype --key-name SmartCode \
    --associate-public-ip-address --security-group-ids sg-xxxxxx \
    --subnet-id subnet-xxxxxx \
    --tag-specifications "ResourceType=instance,Tags=[{Key=MachineId,Value=$machineid}]"

instancedid=`aws ec2 describe-instances --query Reservations[].Instances[].InstanceId --filters Name=tag:MachineId,Values=$machineid`

ip=""
while [ "$ip" = "" ]
do
    echo "Checking IP..."
    ip=`aws ec2 describe-instances --query Reservations[].Instances[].NetworkInterfaces[].Association.PublicIp --filters Name=tag:MachineId,Values=$machineid`
    sleep 2
done

echo $ip

sshcheck=""
while [ "$sshcheck" = "" ]
do
    echo "Checking SSH..."
    sshcheck=`ssh -i SmartCode.pem -o ConnectTimeout=5 -o StrictHostKeyChecking=no ubuntu@$ip "ls /"`
done

echo "Copying files and running commands..."

scpcmd="scp -i SmartCode.pem -o StrictHostKeyChecking=no"
sshcmd="ssh -i SmartCode.pem -o StrictHostKeyChecking=no ubuntu@$ip"

$scpcmd benchmark/cpubenchmark.cpp ubuntu@$ip:
$scpcmd benchmark/Makefile ubuntu@$ip:
$sshcmd "make"
$sshcmd "sudo apt-get install -y awscli parallel"
$sshcmd "mkdir -p ~/.aws"
$scpcmd ~/.aws/config ubuntu@$ip:.aws
$scpcmd ~/.aws/credentials ubuntu@$ip:.aws
$scpcmd benchmark/run.sh ubuntu@$ip:

echo "SSH command:"
echo $sshcmd

$sshcmd "bash ./run.sh $taskids"

aws ec2 terminate-instances --instance-ids $instanceid

