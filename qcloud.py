#!/usr/bin/env python3
# -*- coding: utf8 -*-
from QcloudApi.qcloudapi import QcloudApi
import os
import json
import yaml



ACTION_SUCCESS = 0
# 设置需要加载的模块
module = 'cns'
# 对应接口的接口名，请参考wiki文档上对应接口的接口名

secretFiles = [os.path.expanduser('~/.config/qcloud/config.yaml'), './config.yaml']
secret = None
for _file in secretFiles:
    if os.path.exists(_file):
        secret = _file

try:
    res = yaml.load(open(secret))
    secretID, secretKey = res['secretID'], res['secretKey']
    default_domain = res.get('default_domain', None)
except:
    raise ValueError("Please check secret files", secretFiles)




# 云API的公共参数
config = {
    'Region': 'ap-guangzhou',
    'secretId': secretID,
    'secretKey': secretKey,
    'method': 'GET',
    'SignatureMethod': 'HmacSHA1',
    # 只有cvm需要填写version，其他产品不需要
    # 'Version': '2017-03-12'
}

# 接口参数，根据实际情况填写，支持json
# 例如数组可以 "ArrayExample": ["1","2","3"]
# 例如字典可以 "DictExample": {"key1": "value1", "key2": "values2"}
action_params = {
    # 'Limit':1,
}

from netaddr.ip import IPAddress
 
def isIP4or6(cfgstr):
    ipFlg = False
 
    if '/' in cfgstr:
        text = cfgstr[:cfgstr.rfind('/')]
    else:
        text = cfgstr
     
    try:
        addr = IPAddress(text)
        ipFlg = True
    except:
        ipFlg = False
 
    if ipFlg == True:
        return addr.version
    else:
        return False
         

    
try:
    service = QcloudApi(module, config)

    # 请求前可以通过下面几个方法重新设置请求的secretId/secretKey/Region/method/SignatureMethod参数
    # 重新设置请求的Region
    #service.setRegion('ap-shanghai')

    # 打印生成的请求URL，不发起请求
    # print(service.generateUrl(action, action_params))
    # 调用接口，发起请求，并打印返回结果
    # print(service.call(action, action_params).decode('utf-8'))
except Exception as e:
    import traceback
    print('traceback.format_exc():\n%s' % traceback.format_exc())

def get_domainList():
    action = "DomainList"
    action_params = {}
    output = json.loads(service.call(action, action_params).decode())
    # print(output, type(output))
    assert output['code'] == ACTION_SUCCESS
    for domain in output['data']['domains']:
        yield domain['name']


def get_recordList(domain, offset=None, length=None, subDomain=None,
        recordType=None, qProjectID=None, value=None):
    assert domain in list(get_domainList()), domain+' not exist'
    action = 'RecordList'
    action_params = {
        'domain': domain,
    }
    if subDomain:
        action_params['subDomain'] = subDomain
    if recordType:
        action_params['recordType'] = recordType
        
        
    output = json.loads(service.call(action, action_params).decode())
    assert output['code'] == ACTION_SUCCESS, output['message']
    if value is not None:
        records = []
        for record in output['data']['records']:
            if record['value'] == value:
                records.append(record)
    else:
        records = output['data']['records']
    return records 

def exist_record(domain, subDomain, recordType, value):
    return len(get_recordList(domain, subDomain=subDomain, recordType=recordType, value=value)) >  0
    
def mod_recordStatus(domain, recordID, status=1):
    assert domain in list(get_domainList()), domain+' not belongs to this user'
    action = 'RecordStatus'
    action_params = {
        'domain' : domain, 
        'recordId': int(recordID),
    }
    if status == 1:
        action_params['status'] = 'enable'
    else:
        action_params['status'] = 'disable'
    print(action_params)
    output = json.loads(service.call(action, action_params).decode())
    assert output['code'] == ACTION_SUCCESS, output['message']

def mod_record(domain, subDomain, recordType='A', recordLine='默认', 
        value=None, ttl=None, mx=None, runtype='mod'):
    """Add/Modify record and enable it"""

    assert domain in list(get_domainList()), domain+' not belongs to this user'
    assert recordType in ["A", "CNAME", "MX", "TXT", "NS", "AAAA", "SRV"]
    assert recordLine in ["默认", "电信","联通", "移动", "海外"]
    assert value is not None, 'value cannot be empty'
    assert ttl is None or int(ttl)
    if recordType == 'MX':
        assert mx is not None, 'MX cannot be empty for MX type'
    if isIP4or6(value) == 4:
        recordType = 'A'
    elif isIP4or6(value) == 6:
        recordType = 'AAAA'
    action_params = {
        'domain': domain,
        'subDomain': subDomain,
        'recordType': recordType,
        'recordLine': recordLine,
        'value': value}

    existence = exist_record(domain, subDomain, recordType, value)
    if existence:
        recordList = get_recordList(domain, subDomain=subDomain, 
            recordType=recordType, value=value)
        print(recordList)
        if recordList[0]['enabled'] == 0:
            mod_recordStatus(domain, recordList[0]['id'], 1)
        return
    recordList = get_recordList(domain, subDomain=subDomain, 
        recordType=recordType)
    if len(recordList)==0 or runtype=='create':
        action = 'RecordCreate'
    else:
        action = 'RecordModify'
        recordID = recordList[0]['id']
        action_params['recordId'] = recordID
    if ttl:
        action_params['ttl'] = ttl
    if mx:
        action_params['mx'] = mx
    print(action_params)
    output = json.loads(service.call(action, action_params).decode())
    assert output['code'] == ACTION_SUCCESS, output['message']


def test():
    dlist = list(get_domainList())
    print(dlist)
    rlist = get_recordList(default_domain)
    print(json.dumps(rlist, indent=4))
    mod_recordStatus(default_domain, 397946975, 1)
    mod_record(default_domain, 'mu', 'A', value='2402:f000:1:1c01:6e92:bfff:fe05:1075')

    print(isIP4or6('1.1.1.1'))
    print(isIP4or6('2402:f000:1::bfff::d002'))
    print(isIP4or6('2402:f000:1::bfff:fe0c:'))


if __name__ == '__main__':
    # test()
    import sys
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--domain')
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()

    if args.test:
        test()
        exit()
    if args.domain is None:
        if default_domain is not None:
            args.domain = default_domain
        else:
            raise ValueError("No default domain provided")

    for line in sys.stdin.readlines():
        if len(line.split()) <= 1:
            continue
        name, ip = line.split()[:2]
        mod_record(args.domain, name, value=ip)
        mod_record(args.domain, name, value=ip)
