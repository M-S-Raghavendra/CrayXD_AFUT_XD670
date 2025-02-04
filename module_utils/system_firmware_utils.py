# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023 Hewlett Packard Enterprise, Inc. All rights reserved.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
import os
__metaclass__ = type
#import pandas as pd
import json
import subprocess
import time
from requests_toolbelt import MultipartEncoder
from ansible_collections.community.general.plugins.module_utils.redfish_utils import RedfishUtils
from ansible.module_utils.urls import open_url, prepare_multipart
from ansible.module_utils.six.moves.urllib.error import URLError, HTTPError
import configparser

supported_models=["XD670"]
#supported_models=["HPE CRAY XD220V", "HPE CRAY SC XD220V", "HPE CRAY XD225V","HPE CRAY SC XD225V", "HPE CRAY XD295V","HPE CRAY SC XD295V", "HPE CRAY XD665", "HPE CRAY XD670",  "HPE CRAY SC XD665", "HPE CRAY SC XD670 DLC", "HPE CRAY SC XD670"]

#to get inventory, update
partial_models={}
#{"HPE CRAY XD670": "XD670", "HPE CRAY XD670 DLC": "XD670", "HPE CRAY XD670 SC": "XD670", "HPE CRAY XD665": "XD665", "HPE CRAY XD665 SC": "XD665", "HPE CRAY XD220v": "XD220"}
supported_targets={
    "XD670": ["BMC", "BMCImage1", "BMCImage2", "BIOS", "BIOS2", "BPB_CPLD1", "BPB_CPLD2", "MB_CPLD1", "SCM_CPLD1", "GPU_ALL", "HGX_FW_BMC_0", "HGX_FW_ERoT_BMC_0", "HGX_FW_ERoT_FPGA_0", "HGX_FW_ERoT_GPU_SXM_1", "HGX_FW_ERoT_GPU_SXM_2", "HGX_FW_ERoT_GPU_SXM_3", "HGX_FW_ERoT_GPU_SXM_4", "HGX_FW_ERoT_GPU_SXM_5", "HGX_FW_ERoT_GPU_SXM_6", "HGX_FW_ERoT_GPU_SXM_7", "HGX_FW_ERoT_GPU_SXM_8", "HGX_FW_ERoT_NVSwitch_0", "HGX_FW_ERoT_NVSwitch_1", "HGX_FW_ERoT_NVSwitch_2", "HGX_FW_ERoT_NVSwitch_3", "HGX_FW_ERoT_PCIeSwitch_0", "HGX_FW_FPGA_0","HGX_FW_GPU_SXM_1","HGX_FW_GPU_SXM_2","HGX_FW_GPU_SXM_3","HGX_FW_GPU_SXM_4","HGX_FW_GPU_SXM_5","HGX_FW_GPU_SXM_6","HGX_FW_GPU_SXM_7","HGX_FW_GPU_SXM_8","HGX_FW_NVSwitch_0","HGX_FW_NVSwitch_1","HGX_FW_NVSwitch_2","HGX_FW_NVSwitch_3","HGX_FW_PCIeRetimer_0","HGX_FW_PCIeRetimer_1","HGX_FW_PCIeRetimer_2","HGX_FW_PCIeRetimer_3","HGX_FW_PCIeRetimer_4","HGX_FW_PCIeRetimer_5","HGX_FW_PCIeRetimer_6","HGX_FW_PCIeRetimer_7","HGX_FW_PCIeSwitch_0","HGX_InfoROM_GPU_SXM_1","HGX_InfoROM_GPU_SXM_2","HGX_InfoROM_GPU_SXM_3","HGX_InfoROM_GPU_SXM_4","HGX_InfoROM_GPU_SXM_5","HGX_InfoROM_GPU_SXM_6","HGX_InfoROM_GPU_SXM_7","HGX_InfoROM_GPU_SXM_8"],
}

XD670_unsupported_targets = ["BMCImage1","BPB_CPLD1", "BPB_CPLD2", "MB_CPLD1", "SCM_CPLD1"] #only of Jakku
#BMCImage1 equivalent to BMC
#BPB_CPLD1 and BPB_CPLD2 together equivalent to BPB_CPLD
#MB_CPLD1 and SCM_CPLD1 together equivalent to MB_CPLD1_SCM_CPLD1

XD670_targets = ['BMC', 'BMCImage1', 'BMCImage2', 'BIOS', 'BIOS2', 'BPB_CPLD1', 'BPB_CPLD2', 'MB_CPLD1', 'SCM_CPLD1']
GPU_targets = ['HGX_FW_BMC_0', 'HGX_FW_ERoT_BMC_0', 'HGX_FW_ERoT_FPGA_0', 'HGX_FW_ERoT_GPU_SXM_1', 'HGX_FW_ERoT_GPU_SXM_2', 'HGX_FW_ERoT_GPU_SXM_3', 'HGX_FW_ERoT_GPU_SXM_4', 'HGX_FW_ERoT_GPU_SXM_5', 'HGX_FW_ERoT_GPU_SXM_6', 'HGX_FW_ERoT_GPU_SXM_7', 'HGX_FW_ERoT_GPU_SXM_8', 'HGX_FW_ERoT_NVSwitch_0', 'HGX_FW_ERoT_NVSwitch_1', 'HGX_FW_ERoT_NVSwitch_2', 'HGX_FW_ERoT_NVSwitch_3', 'HGX_FW_ERoT_PCIeSwitch_0', 'HGX_FW_FPGA_0', 'HGX_FW_GPU_SXM_1', 'HGX_FW_GPU_SXM_2', 'HGX_FW_GPU_SXM_3', 'HGX_FW_GPU_SXM_4', 'HGX_FW_GPU_SXM_5', 'HGX_FW_GPU_SXM_6', 'HGX_FW_GPU_SXM_7', 'HGX_FW_GPU_SXM_8', 'HGX_FW_NVSwitch_0', 'HGX_FW_NVSwitch_1', 'HGX_FW_NVSwitch_2', 'HGX_FW_NVSwitch_3', 'HGX_FW_PCIeRetimer_0', 'HGX_FW_PCIeRetimer_1', 'HGX_FW_PCIeRetimer_2', 'HGX_FW_PCIeRetimer_3', 'HGX_FW_PCIeRetimer_4', 'HGX_FW_PCIeRetimer_5', 'HGX_FW_PCIeRetimer_6', 'HGX_FW_PCIeRetimer_7', 'HGX_FW_PCIeSwitch_0', 'HGX_InfoROM_GPU_SXM_1', 'HGX_InfoROM_GPU_SXM_2', 'HGX_InfoROM_GPU_SXM_3', 'HGX_InfoROM_GPU_SXM_4', 'HGX_InfoROM_GPU_SXM_5', 'HGX_InfoROM_GPU_SXM_6', 'HGX_InfoROM_GPU_SXM_7', 'HGX_InfoROM_GPU_SXM_8']

reboot = {
    "BIOS": ["AC_PC_redfish"],
    "BIOS2": ["AC_PC_redfish"],
}

routing = {
    "XD220V": "0x34 0xa2 0x00 0x19 0xA9",
    "XD225V": "0x34 0xa2 0x00 0x19 0xA9",
    "XD295V": "0x34 0xa2 0x00 0x19 0xA9",
    "XD665": "0x34 0xA2 0x00 0x19 0xa9 0x00",
    ###"XD670": ""
}

#config = configparser.ConfigParser()

class CrayRedfishUtils(RedfishUtils):
    def post_multi_request(self, uri, headers, payload):
        username, password, basic_auth = self._auth_params(headers)
        try:
            resp = open_url(uri, data=payload, headers=headers, method="POST",
                            url_username=username, url_password=password,
                            force_basic_auth=basic_auth, validate_certs=False,
                            follow_redirects='all',
                            use_proxy=True, timeout=self.timeout)
            resp_headers = dict((k.lower(), v) for (k, v) in resp.info().items())
            return True
        except Exception as e:
            return False

    def get_model(self):
        try:
            response = self.get_request(self.root_uri + "/redfish/v1/Systems/Self")
            if response['ret'] is False:
                return "NA"
        except:
            return "NA"
        model="NA"
        try:
            if 'Model' in response['data']:
                model = response['data'][u'Model'].strip()
        except:
            if 'Model' in response:
                model = response[u'Model'].strip()
            else:
                return "NA"
        if model not in partial_models and "XD" in model:
            split_model_array = model.split() #["HPE", "Cray", "XD665"]
            for dum in split_model_array:
                if "XD" in dum:
                    partial_models[model.upper()]=dum.upper()
        return model

    def power_state(self):
        response = self.get_request(self.root_uri + "/redfish/v1/Systems/Self")
        if response['ret'] is False:
            return "NA"
        state='None'
        try:
            if 'PowerState' in response['data']:
                state = response['data'][u'PowerState'].strip()
        except:
            if 'PowerState' in response:
                state = response[u'PowerState'].strip()
        return state

    def power_on(self):
        payload = {"ResetType": "On"}
        target_uri = "/redfish/v1/Systems/Self/Actions/ComputerSystem.Reset"
        response1 = self.post_request(self.root_uri + target_uri, payload)
        time.sleep(120)

    def power_off(self):
        payload = {"ResetType": "ForceOff"}
        target_uri = "/redfish/v1/Systems/Self/Actions/ComputerSystem.Reset"
        response1 = self.post_request(self.root_uri + target_uri, payload)
        time.sleep(120)

    def get_PS_CrayXD670(self,attr):
        ini_path = os.path.join(os.getcwd(),'config.ini')
        config = configparser.ConfigParser()
        IP = attr.get('baseuri')
        config.read(ini_path)
        try:
            option = config.get('Options','power_state')
            if option=="":
                return {'ret': False, 'changed': True, 'msg': 'Must specify the required option for power_state in config.ini'}
        except:
            return {'ret': False, 'changed': True, 'msg': 'Must specify the required option for power_state in config.ini'}

        csv_file_name = attr.get('output_file_name')
        if not os.path.exists(csv_file_name):
            f = open(csv_file_name, "w")
            to_write="IP_Address,Model,Power_State\n"
            f.write(to_write)
            f.close()
        model = self.get_model()
        if "XD670" in model.upper():
            power_state = self.power_state()
            if option.upper()=="NA":
                lis=[IP,model,power_state]
            elif option.upper()=="ON":
                if power_state.upper()=="OFF":
                    self.power_on()
                power_state = self.power_state()
                lis=[IP,model,power_state]
            elif option.upper()=="OFF":
                if power_state.upper()=="ON":
                    self.power_off()
                power_state = self.power_state()
                lis=[IP,model,power_state]
            else:
                return {'ret': False, 'changed': True, 'msg': 'Must specify the correct required option for power_state in config.ini'}

        else:
            lis=[IP,model,"unsupported_model"]
        new_data=",".join(lis)
        return {'ret': True,'changed': True, 'msg': str(new_data)}


    def target_supported(self,model,target,image_type):
        try:
            if 'HMC' in image_type:
                return True
            if 'RCU' in image_type:
                return True
            elif target in supported_targets[partial_models[model.upper()]]:
                return True
            return False
        except:
            return False

    def get_fw_version(self,target):
        try:
            response = self.get_request(self.root_uri + "/redfish/v1/UpdateService/FirmwareInventory"+"/"+target)
            if response['ret'] is False:
                return "NA"
            try:
                version = response['data']['Version']
                return version
            except:
                version = response['Version']
                return version
        except:
            return "NA"

    def bmcfreememory(self):
        payload = {}
        target_uri = "/redfish/v1/UpdateService/Action/Oem/Gbt/HMCUpdate.PrepareFreeMemory"
        response = self.post_request(self.root_uri + target_uri, payload)
        return response

    def AC_PC_redfish(self):
        payload = {"ResetType": "ForceRestart"}
        target_uri = "/redfish/v1/Systems/Self/Actions/ComputerSystem.Reset"
        response1 = self.post_request(self.root_uri + target_uri, payload)
        time.sleep(180)
        target_uri = "/redfish/v1/Chassis/Self/Actions/Chassis.Reset"
        response2 = self.post_request(self.root_uri + target_uri, payload)
        time.sleep(180)
        return response1 or response2

    def AC_PC_ipmi(self, IP, username, password, routing_value):
        try:
            command='ipmitool -I lanplus -H '+IP+' -U '+username+' -P '+password+' raw '+ routing_value
            subprocess.run(command, shell=True, check=True, timeout=15)
            time.sleep(300)
            self.power_on()
            return True
        except:
            return False
    def get_gpu_inventory(self,attr):
        IP = attr.get('baseuri')
        csv_file_name = attr.get('output_file_name')
        model = self.get_model()
        if not os.path.exists(csv_file_name):
            f = open(csv_file_name, "w")
            to_write="IP_Address,Model,HGX_FW_BMC_0,HGX_FW_ERoT_BMC_0,HGX_FW_ERoT_FPGA_0,HGX_FW_ERoT_GPU_SXM_1,HGX_FW_ERoT_GPU_SXM_2,HGX_FW_ERoT_GPU_SXM_3,HGX_FW_ERoT_GPU_SXM_4,HGX_FW_ERoT_GPU_SXM_5,HGX_FW_ERoT_GPU_SXM_6,HGX_FW_ERoT_GPU_SXM_7,HGX_FW_ERoT_GPU_SXM_8,HGX_FW_ERoT_NVSwitch_0,HGX_FW_ERoT_NVSwitch_1,HGX_FW_ERoT_NVSwitch_2,HGX_FW_ERoT_NVSwitch_3,HGX_FW_ERoT_PCIeSwitch_0,HGX_FW_FPGA_0,HGX_FW_GPU_SXM_1,HGX_FW_GPU_SXM_2,HGX_FW_GPU_SXM_3,HGX_FW_GPU_SXM_4,HGX_FW_GPU_SXM_5,HGX_FW_GPU_SXM_6,HGX_FW_GPU_SXM_7,HGX_FW_GPU_SXM_8,HGX_FW_NVSwitch_0,HGX_FW_NVSwitch_1,HGX_FW_NVSwitch_2,HGX_FW_NVSwitch_3,HGX_FW_PCIeRetimer_0,HGX_FW_PCIeRetimer_1,HGX_FW_PCIeRetimer_2,HGX_FW_PCIeRetimer_3,HGX_FW_PCIeRetimer_4,HGX_FW_PCIeRetimer_5,HGX_FW_PCIeRetimer_6,HGX_FW_PCIeRetimer_7,HGX_FW_PCIeSwitch_0,HGX_InfoROM_GPU_SXM_1,HGX_InfoROM_GPU_SXM_2,HGX_InfoROM_GPU_SXM_3,HGX_InfoROM_GPU_SXM_4,HGX_InfoROM_GPU_SXM_5,HGX_InfoROM_GPU_SXM_6,HGX_InfoROM_GPU_SXM_7,HGX_InfoROM_GPU_SXM_8\n"
            all_targets = GPU_targets
            f.write(to_write)
            f.close()
        entry=[]
        entry.append(IP)
        if model=="NA":
            entry.append("unreachable/unsupported_system") #unreachable or not having model field correctly, i.e not even a XD system
            for target in GPU_targets:
                entry.append("NA")
        elif partial_models[model.upper()] not in supported_models: #might be a Cray XD like XD685 which is not yet supported
            entry.append("unsupported_model, ")
            for target in GPU_targets:
                entry.append("NA")
            #return {'ret': True, 'changed': True, 'msg': 'Must specify systems of only the supported models. Please check the model of %s'%(IP)}
        else:
            entry.append(model)
            for target in GPU_targets:
                if target in supported_targets[partial_models[model.upper()]]:
                    version=self.get_fw_version(target)
                else:
                    version = "NA"
                entry.append(version)
        new_data=",".join(entry)
        return {'ret': True,'changed': True, 'msg': str(new_data)}

    def get_sys_fw_inventory(self,attr):
        IP = attr.get('baseuri')
        csv_file_name = attr.get('output_file_name')
        model = self.get_model()
        if not os.path.exists(csv_file_name):
            f = open(csv_file_name, "w")
            to_write="IP_Address,Model,BMC,BMCImage1,BMCImage2,BIOS,BIOS2,BPB_CPLD1,BPB_CPLD2,MB_CPLD1,SCM_CPLD1\n"
            f.write(to_write)
            f.close()
        entry=[]
        entry.append(IP)
        if model=="NA":
            entry.append("unreachable/unsupported_system") #unreachable or not having model field correctly, i.e not even a XD system
            for target in XD670_targets:
                entry.append("NA")
        elif partial_models[model.upper()] not in supported_models: #might be a Cray XD like XD685 which is not yet supported
            entry.append("unsupported_model, ")
            for target in XD670_targets:
                entry.append("NA")
            #return {'ret': True, 'changed': True, 'msg': 'Must specify systems of only the supported models. Please check the model of %s'%(IP)}
        else:
            entry.append(model)
            for target in XD670_targets:
                if target in supported_targets[partial_models[model.upper()]]:
                    version=self.get_fw_version(target)
                else:
                    version = "NA"
                entry.append(version)
        new_data=",".join(entry)
        return {'ret': True,'changed': True, 'msg': str(new_data)}

    def helper_update_GPU(self,update_status,target,image_path,image_type,IP,username,password,model):
        update_status="Update failed"
        response = self.get_request(self.root_uri + "/redfish/v1/UpdateService")
        if response['ret'] is False:
            update_status="UpdateService api not found"
            return update_status
        else:
            data = response['data']
            if 'MultipartHttpPushUri' in data:
                headers = {'Expect': 'Continue','Content-Type': 'multipart/form-data'}
                body = {}
                if target=="GPU_ALL" and "fwpkg" in image_path:
                    response_memory = self.bmcfreememory()
                    if not response_memory:
                        update_status="BMC free memory failed"
                    else:
                        data_memory = response_memory['data']
                        if 'Status' in data_memory and data_memory['Status'] == 'Success':
                            targets_uri='/redfish/v1/UpdateService/FirmwareInventory/HGX_FW_BMC_0'
                            body['UpdateParameters'] = (None, json.dumps({"Targets": [targets_uri]}), 'application/json')
                            body['OemParameters'] = (None, json.dumps({"ImageType": image_type}) , 'application/json')
                            with open(image_path, 'rb') as image_path_rb:
                                body['UpdateFile'] = (image_path, image_path_rb,'application/octet-stream' )
                                encoder = MultipartEncoder(body)
                                body = encoder.to_string()
                                headers['Content-Type'] = encoder.content_type
                                response = self.post_multi_request(self.root_uri + "/redfish/v1/UpdateService/upload",
                                                           headers=headers, payload=body)
                                if response is False:
                                    update_status="failed_Post"
                                else:
                                    update_status="success"
                        else:
                            update_status="Memory insufficient for firmware update"
            return update_status

    def helper_update(self,update_status,target,image_path,image_type,IP,username,password,model):
        before_version=None
        after_version=None
        update_status=None
        if target!="BPB_CPLD" and target!="SCM_CPLD1" and target!="MB_CPLD1":
            before_version = self.get_fw_version(target)
            if target=="BMC" and "XD670" in model.upper() and "NA" in before_version:
                target="BMCImage1"
                before_version = self.get_fw_version(target)
            #after_version=None
        else:
            before_version = "NotApplicable"
            after_version="NotApplicable"
        if not before_version.startswith("NA"):
            #proceed for update
            response = self.get_request(self.root_uri + "/redfish/v1/UpdateService")
            if response['ret'] is False:
                update_status="UpdateService api not found"
            else:
                data = response['data']
                if 'MultipartHttpPushUri' in data:
                    headers = {'Expect': 'Continue','Content-Type': 'multipart/form-data'}
                    body = {}
                    if target!="BPB_CPLD":
                        targets_uri='/redfish/v1/UpdateService/FirmwareInventory/'+target+'/'
                        body['UpdateParameters'] = (None, json.dumps({"Targets": [targets_uri]}), 'application/json')
                    else:
                        image_type = "BPB_CPLD"
                        BPB_target = ['/redfish/v1/UpdateService/FirmwareInventory/BPB_CPLD1']
                        body['UpdateParameters'] = (None, json.dumps({"Targets": BPB_target}), 'application/json')
                    body['OemParameters'] = (None, json.dumps({"ImageType": image_type}) , 'application/json')
                    with open(image_path, 'rb') as image_path_rb:
                        body['UpdateFile'] = (image_path, image_path_rb,'application/octet-stream' )
                        encoder = MultipartEncoder(body)
                        body = encoder.to_string()
                        headers['Content-Type'] = encoder.content_type
                        response = self.post_multi_request(self.root_uri + data['MultipartHttpPushUri'],
                                                    headers=headers, payload=body)
                        if response is False:
                            update_status="failed_Post"
                            after_version="NA"
                        else:
                            #add time.sleep (for BMC to comeback after flashing )
                            time.sleep(500)
                            #call reboot logic based on target
                            update_status="success"
                            if target in reboot:
                                what_reboots = reboot[target]
                                for reb in what_reboots:
                                    if reb=="AC_PC_redfish":
                                        result=self.AC_PC_redfish()
                                        if not result:
                                            update_status="reboot_failed"
                                            break
                                        time.sleep(300)
                                    elif reb=="AC_PC_ipmi":
                                        result = self.AC_PC_ipmi(IP, username, password, routing[partial_models[model.upper()]]) #based on the model end routing code changes
                                        if not result:
                                            update_status="reboot_failed"
                                            break
                            if update_status.lower()=="success":
                                #call version of respective target and store versions after update
                                time.sleep(180) #extra time requiring as of now for systems under test
                                if target!="BPB_CPLD" and target!="SCM_CPLD1" and target!="MB_CPLD1" and target!="GPU":
                                    after_version=self.get_fw_version(target)
                            else:
                                if target!="BPB_CPLD" and target!="SCM_CPLD1" and target!="MB_CPLD1" and target!="GPU":
                                    after_version="NA"

            if target!="BPB_CPLD" and target!="SCM_CPLD1" and target!="MB_CPLD1":
                return before_version,after_version,update_status
            else:
                return update_status
        else:
            update_status="NA"
            if target!="BPB_CPLD" and target!="SCM_CPLD1" and target!="MB_CPLD1":
                after_version="NA"
                return before_version,after_version,update_status
            else:
                return update_status

    def system_fw_update(self, attr):
        ini_path = os.path.join(os.getcwd(),'config.ini')
        config = configparser.ConfigParser()
        config.read(ini_path)
        key = ""
        try:
            target = config.get('Target','update_target')
            image_path_inputs = {
                "XD670": config.get('Image', 'update_image_path_xd670'),
                }
        except:
            pass

        ## have a check that at least one image path set based out of the above new logic
        if not any(image_path_inputs.values()):
            return {'ret': False, 'changed': True, 'msg': 'Must specify at least one update_image_path'}
        IP = attr.get('baseuri')
        username = attr.get('username')
        password = attr.get('password')
        update_status = "success"
        before_version=None
        after_version=None
        is_target_supported=False
        # before_version="NA"
        # after_version="NA"
        image_path="NA"
        csv_file_name = attr.get('output_file_name')
        image_type = "HPM"

        if target=="" or target.upper() in XD670_unsupported_targets:
            return {'ret': False, 'changed': True, 'msg': 'Must specify the correct target for firmware update'}    
        model = self.get_model()

        if not os.path.exists(csv_file_name):
            f = open(csv_file_name, "w")
            if target=="BPB_CPLD" or target=="SCM_CPLD1_MB_CPLD1":
                to_write="IP_Address,Model,Update_Status,Remarks\n"
            elif target=="GPU_ALL":
                to_write="IP_Address,Model,Update_Status,Remarks\n"
            else:
                to_write="IP_Address,Model,"+target+'_Pre_Ver,'+target+'_Post_Ver,'+"Update_Status\n"
            f.write(to_write)
            f.close()
        if model=="NA":
            update_status="unreachable/unsupported_system"
            if target=="SCM_CPLD1_MB_CPLD1" or target=="BPB_CPLD":
                lis=[IP,model,update_status,"NA"]
            else:
                lis=[IP,model,"NA","NA",update_status]
            new_data=",".join(lis)
            return {'ret': True,'changed': True, 'msg': str(new_data)}
        elif partial_models[model.upper()] not in supported_models:
            update_status="unsupported_model"
            if target=="SCM_CPLD1_MB_CPLD1" or target=="BPB_CPLD":
                lis=[IP,model,update_status,"NA"]
            else:
                lis=[IP,model,"NA","NA",update_status]
            new_data=",".join(lis)
            return {'ret': True,'changed': True, 'msg': str(new_data)}
        else:
            image_path = image_path_inputs[partial_models[model.upper()]]
            if "XD670" in model and "CPLD" in target.upper():
                if target.upper()=="BPB_CPLD":
                    is_target_supported=True
                power_state = self.power_state()
                if power_state.lower() != "on":
                    update_status="NA"
                    lis=[IP,model,update_status,"node is not ON, please power on the node using the playbook power_state_XD670.yml"]
                    new_data=",".join(lis)
                    return {'ret': True,'changed': True, 'msg': str(new_data)}
                    #return {'ret': False, 'changed': True,'msg': 'System Firmware Update skipped due to powered off state of the node for Cray XD 670, Node needs to be powered on for CPLD firmware updates'}
                elif target=='SCM_CPLD1_MB_CPLD1':
                    is_target_supported=True
                    image_paths=image_path_inputs["XD670"].split()
                    if len(image_paths)!=2:
                        return {'ret': False, 'changed': True,'msg': 'Must specify exactly 2 image_paths, first for SCM_CPLD1 of Cray XD670 and second for MB_CPLD1 of Cray XD670'}
                    for img_path in image_paths:
                        if not os.path.isfile(img_path):
                            #update_status = "fw_file_absent"
                            return {'ret': False, 'changed': True,'msg': 'Must specify correct image_paths for SCM_CPLD1_MB_CPLD1, first for SCM_CPLD1 of Cray XD670 and second for MB_CPLD1 of Cray XD670'}

            if target!="SCM_CPLD1_MB_CPLD1" and not os.path.isfile(image_path):
                update_status = "NA_fw_file_absent"
                if target=="BPB_CPLD":
                    lis=[IP,model,update_status,"NA"]
                else:
                    lis=[IP,model,"NA","NA",update_status]
                new_data=",".join(lis)
                return {'ret': False,'changed': True, 'msg': 'NA_fw_file_absent'}
            else:
                if target!="SCM_CPLD1_MB_CPLD1" and target!="BPB_CPLD":
                        is_target_supported = self.target_supported(model,target,image_type)
                if not is_target_supported:
                    update_status="target_not_supported"
                    if target=="SCM_CPLD1_MB_CPLD1" or target=="BPB_CPLD":
                        lis=[IP,model,update_status,"NA"]
                    else:
                        lis=[IP,model,"NA","NA",update_status]
                    new_data=",".join(lis)
                    return {'ret': True,'changed': True, 'msg': str(new_data)}
                else:
                    #call version of respective target and store versions before update
                    if target=="SCM_CPLD1_MB_CPLD1":
                        update_status=self.helper_update(update_status,"SCM_CPLD1",image_paths[0],"SCM_CPLD",IP,username,password,model)
                        if update_status.lower()=="success": #SCM has updates successfully, proceed for MB_CPLD1 update
                            #check node to be off -- call power_off_node funcn
                            power_state = self.power_state()
                            if power_state.lower() == "on":
                                self.power_off()
                                power_state = self.power_state()
                                if power_state.lower() == "on":
                                    lis=[IP,model,"NA","MB_CPLD1 requires node off, tried powering off the node, but failed to power off"] #unable to power off node for MB_CPLD1
                                else:
                                    update_status=self.helper_update(update_status,"MB_CPLD1",image_paths[1],"MB_CPLD",IP,username,password,model)
                                    if update_status.lower() == "success":
                                        remarks="Please plug out and plug in power cables physically"
                                    else:
                                        remarks="Please reflash the firmware and DO NOT DO physical power cycle"
                            lis=[IP,model,update_status,remarks]
                        else:
                            remarks="Please reflash the firmware and DO NOT DO physical power cycle"
                            lis=[IP,model,update_status,remarks]
                    elif target=="BPB_CPLD":
                        update_status=self.helper_update(update_status,target,image_path,image_type,IP,username,password,model)
                        if update_status.lower() == "success":
                            remarks="Please plug out and plug in power cables physically"
                        else:
                            remarks="Please reflash the firmware and DO NOT DO physical power cycle"
                        lis=[IP,model,update_status,remarks]
                    elif "GPU_ALL" in target:
                        update_status=self.helper_update_GPU(update_status,target,image_path,"HMC",IP,username,password,model)
                        if update_status.lower() == "success":
                            update_status="Update Triggered"
                            remarks="It will take nearly 30 to 40 minutes to update baseboard firmware. The target system will be reboot once the firmware update procedure completed"
                        else:
                            remarks="Perform BMC reset to free memory and Power cycle the system, try again once the system is up"
                        lis=[IP,model,update_status,remarks]
                    else:
                        if target=="BMC" and "XD670_BMC" not in image_path or target=="BMCImage1" and "XD670_BMC" not in image_path or target=="BMCImage2" and "XD670_BMC" not in image_path:
                            return {'ret': False, 'changed': True, 'msg': 'Must specify correct image and target'}
                        elif target=="BIOS" and "CUXD670" not in image_path or target=="BIOS2" and "CUXD670" not in image_path:
                            return {'ret': False, 'changed': True, 'msg': 'Must specify correct image and target'}
                        bef_ver,aft_ver,update_status=self.helper_update(update_status,target,image_path,image_type,IP,username,password,model)
                        lis=[IP,model,bef_ver,aft_ver,update_status]
                    new_data=",".join(lis)
                    return {'ret': True,'changed': True, 'msg': str(new_data)}
