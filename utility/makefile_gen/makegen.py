#!/usr/bin/env python
from sys import argv
import json
import glob
import os
import subprocess

def create_params(target,data):
    target.write("#+-------------------------------------------------------------------------------\n")
    target.write("# The following parameters are assigned with default values. These parameters can\n")
    target.write("# be overridden through the make command line\n")
    target.write("#+-------------------------------------------------------------------------------\n")
    target.write("\n")

    target.write("# Run Target:\n")
    target.write("#   hw  - Compile for hardware\n")
    target.write("#   sw_emu/hw_emu - Compile for software/hardware emulation\n")
    target.write("# FPGA Board Platform (Default ~ ku115)\n")

    target.write("\n")
    
    target.write("# Points to Utility Directory\n")
    target.write("COMMON_REPO = ../../../\n")
    target.write("ABS_COMMON_REPO = $(shell readlink -f $(COMMON_REPO))\n")
    target.write("\n")
    target.write("include ./utils.mk\n")
    target.write("REPORT := no\n")
    target.write("PROFILE := no\n")
    target.write("DEBUG := no\n")

    target.write("\n")
    target.write("TARGETS := hw\n")
    target.write("TARGET := $(TARGETS)\n")
    if "board" in data:
        target.write("DEVICES := ")
        target.write(data["board"][0])
    elif "nboard" in data:
        target.write("DEVICES := ")
        if "xilinx_kcu1500_dynamic_5_0" not in data["nboard"]:
            target.write("xilinx_kcu1500_dynamic_5_0\n")
        else:
            target.write("xilinx_kcu1500_dynamic_5_0\n")
    else:
        target.write("DEVICES := ")
        target.write("xilinx_kcu1500_dynamic_5_0\n")
    target.write("DEVICE := $(DEVICES)\n")
    target.write("XCLBIN := ./xclbin\n")
    target.write("DSA := $(call device2sandsa, $(DEVICE))\n")
    target.write("\n")

    target.write("CXX := ")
    target.write("$(XILINX_SDX)/bin/xcpp\n")
    target.write("XOCC := ")
    target.write("$(XILINX_SDX)/bin/xocc\n")
    target.write("\n")

    target.write("CXXFLAGS := $(opencl_CXXFLAGS) -Wall -O0 -g -std=c++14\n")
    target.write("LDFLAGS := $(opencl_LDFLAGS)\n")
    target.write("\n")
    return

def add_libs(target, data):
    target.write("#Include Libraries\n")
    target.write("include $(ABS_COMMON_REPO)/libs/opencl/opencl.mk\n")
    if "libs" in data:
        for lib in data["libs"]:
            target.write("include $(ABS_COMMON_REPO)/libs/")
            target.write(lib)
            target.write("/")
            target.write(lib)
            target.write(".mk")
            target.write("\n")
        #for lib in data["libs"]:
        target.write("CXXFLAGS +=")
        for lib in data["libs"]:
            target.write(" $(")
            target.write(lib)
            target.write("_CXXFLAGS)")
        target.write("\n")
        target.write("LDFLAGS +=")
        for lib in data["libs"]:
            target.write(" $(")
            target.write(lib)
            target.write("_LDFLAGS)")
        target.write("\n")
        target.write("HOST_SRCS +=")
        for lib in data["libs"]:
            target.write(" $(")
            target.write(lib)
            target.write("_SRCS)")
    target.write("\n\n")

    return

def add_host_flags(target, data):
    target.write("HOST_SRCS = ")
    target.write("src/host.cpp\n\n")
    target.write("# Host compiler global settings\n")
    target.write("CXXFLAGS = ")
    target.write("-I $(XILINX_SDX)/runtime/include/1_2/ -I/$(XILINX_SDX)/Vivado_HLS/include/ ")
    target.write("-O0 -g -Wall -fmessage-length=0 -std=c++14\n")
    target.write("LDFLAGS = ")
    target.write("-lOpenCL -lpthread -lrt -lstdc++ ")
    target.write("-L$(XILINX_SDX)/runtime/lib/x86_64\n\n")

    return

def add_kernel_flags(target, data):
    target.write("# Kernel compiler global settings\n")
    target.write("CLFLAGS = ")
    target.write("-t $(TARGET) --platform $(DEVICE) --save-temps \n")
    target.write("CLFLAGS += ")
    target.write('--xp "param:compiler.preserveHlsOutput=1" --xp "param:compiler.generateExtraRunData=true"\n')

    if "containers" in data:
        for con in data["containers"]:
            for acc in con["accelerators"]:
                if "max_memory_ports" in acc:
                    target.write("--max_memory_ports ")
                    target.write(acc["name"])
        target.write("\n")

    if "accelerators" in data:
        for acc in data["accelerators"]:
            if "max_memory_ports" in acc:
                target.write("--max_memory_ports ")
                target.write(acc["name"])
        target.write("\n")

    if "containers" in data:
        for con in data["containers"]:
            for acc in con["accelerators"]:
                if "clflags" in acc:
                    flagsplt = acc["clflags"].split()
                    target.write("CLFLAGS += ")
                    target.write(flagsplt[0])
                    target.write(' "%s"' %flagsplt[1])
        target.write("\n")
    if "accelerators" in data:
        for acc in data["accelerators"]:
            if "clflags" in acc:
                flagsplt = acc["clflags"].split()
                target.write("CLFLAGS += ")
                target.write(flagsplt[0])
                target.write(' "%s"' %flagsplt[1])
        target.write("\n")

    if "compiler" in data:
        target.write("CXXFLAGS += ")
        target.write(data["compiler"]["options"])
        target.write("\n\n")

    if "containers" in data:
        for con in data["containers"]:
            if  "ldclflags" in con:
                target.write("# Kernel linker flags\n")
                target.write("LDCLFLAGS = ")
                target.write(con["ldclflags"])
        target.write("\n")
    
    target.write("#'estimate' for estimate report generation\n")
    target.write("#'system' for system report generation\n")
    target.write("ifneq ($(REPORT), no)\n")
    target.write("CLFLAGS += --report estimate\n")
    target.write("CLLDFLAGS += --report system\n")
    target.write("endif\n")
    target.write("\n")

    target.write("#Generates profile summary report\n")
    target.write("ifeq ($(PROFILE), yes)\n")
    target.write("CLFLAGS += --profile_kernel data:all:all:all\n")
    target.write("endif\n")
    target.write("\n")

    target.write("#Generates debug summary report\n")
    target.write("ifeq ($(DEBUG), yes)\n")
    target.write("CLFLAGS += --dk protocol:all:all:all\n")
    target.write("endif\n")
    target.write("\n")

    target.write("EXECUTABLE = ")
    '''if "containers" in data:
        target.write(data["containers"][0]["name"])
    elif "accelerators" in data:
        target.write(data["accelerators"][0]["name"])
    else:'''
    target.write("host")

    target.write("\n\n")

    return

def add_containers(target, data):
    container_name = 0
    acc_cnt = 0
    bin_cnt = 0
    if "containers" in data:
        for dictionary in data["containers"]:
            if dictionary["accelerators"]:
                acc_cnt = acc_cnt + 1 
            if dictionary["name"]:
                bin_cnt = bin_cnt + 1 
        for con in data["containers"]:
            target.write("BINARY_CONTAINERS += $(XCLBIN)/")
            target.write(data["containers"][container_name]["name"])
            target.write(".$(TARGET).$(DSA)")
            target.write(".xclbin\n")
            for acc in con["accelerators"]:
                if acc_cnt==2 and bin_cnt==2:
                    target.write("BINARY_CONTAINER_")
                    target.write(data["containers"][container_name]["name"])
                    target.write("_OBJS += $(XCLBIN)/")
                else:
                    target.write("BINARY_CONTAINER_1_OBJS += $(XCLBIN)/")
                target.write(data["containers"][container_name]["name"])
                target.write(".$(TARGET).$(DSA)")
                target.write(".xo\n")
                target.write("ALL_KERNEL_OBJS += $(XCLBIN)/")
                target.write(data["containers"][container_name]["name"])
                target.write(".$(TARGET).$(DSA)")
                target.write(".xo\n")
            container_name = container_name + 1
        target.write("\n")

    else:
        if "accelerators" in data:
            target.write("BINARY_CONTAINERS += $(XCLBIN)/")
            xclbin_name = data["accelerators"][0]["location"].split("/")[1].split(".")[0]
            target.write(xclbin_name)
            target.write(".$(TARGET).$(DSA)")
            target.write(".xclbin\n")
            for acc in data["accelerators"]:
                target.write("BINARY_CONTAINER_1_OBJS += $(XCLBIN)/")
                target.write(acc["name"])
                target.write(".$(TARGET).$(DSA)")
                target.write(".xo\n")
                target.write("ALL_KERNEL_OBJS += $(XCLBIN)/")
                target.write(acc["name"])
                target.write(".$(TARGET).$(DSA)")
                target.write(".xo\n")
            target.write("\n")

    return


def building_kernel(target, data):
    target.write("# Building kernel\n")
    container_name = 0
    if "containers" in data:
        for con in data["containers"]:
            for acc in con["accelerators"]:
                target.write("$(XCLBIN)/")
                target.write(data["containers"][container_name]["name"])
                target.write(".$(TARGET).$(DSA)")
                target.write(".xo: ./")
                target.write(acc["location"])
                target.write("\n")
                target.write("\tmkdir -p $(XCLBIN)\n")
                target.write("\t$(XOCC) $(CLFLAGS) -c -k ")
                target.write(acc["name"])
                target.write(" -I'$(<D)'")
                target.write(" -o'$@' '$<'\n")
            container_name = container_name + 1    
        target.write("\n")
    else:
        if "accelerators" in data:
            for acc in data["accelerators"]:
                target.write("$(XCLBIN)/")
                target.write(acc["name"])
                target.write(".$(TARGET).$(DSA)")
                target.write(".xo: ./")
                target.write(acc["location"])
                target.write("\n")
                target.write("\tmkdir -p $(XCLBIN)\n")
                target.write("\t$(XOCC) $(CLFLAGS) -c -k ")
                target.write(acc["name"])
                target.write(" -I'$(<D)'")
                target.write(" -o'$@' '$<'\n")
        target.write("\n")
    if "containers" in data:
        container_name = 0 
        acc_cnt = 0
        bin_cnt = 0
        for dictionary in data["containers"]:
            if dictionary["accelerators"]:
                acc_cnt = acc_cnt + 1 
            if dictionary["name"]:
                bin_cnt = bin_cnt + 1 
        for con in data["containers"]:
            target.write("$(XCLBIN)/")
            target.write(data["containers"][container_name]["name"])
            if acc_cnt==2 and bin_cnt==2:
                target.write(".$(TARGET).$(DSA)")
                target.write(".xclbin: $(BINARY_CONTAINER_")
                target.write(data["containers"][container_name]["name"])
                target.write("_OBJS)\n")
            else:                
               target.write(".$(TARGET).$(DSA)")
               target.write(".xclbin: $(BINARY_CONTAINER_1_OBJS)\n")
            target.write("\t$(XOCC) $(CLFLAGS) -l $(LDCLFLAGS)")
            for acc in con["accelerators"]:
                target.write(" --nk ")
                target.write(acc["name"])
                target.write(":1")
            target.write(" -o'$@' $(+)\n")
            container_name = container_name + 1    
    else:
        if "accelerators" in data:
            target.write("$(XCLBIN)/")
            xclbin_name = data["accelerators"][0]["location"].split("/")[1].split(".")[0]
            target.write(xclbin_name)
            target.write(".$(TARGET).$(DSA)")
            target.write(".xclbin: $(BINARY_CONTAINER_1_OBJS)\n")
            target.write("\t$(XOCC) $(CLFLAGS) -l $(LDCLFLAGS)")
            for acc in data["accelerators"]:
                target.write(" --nk ")
                target.write(acc["name"])
                target.write(":1")
            target.write(" -o'$@' $(+)\n")
    target.write("\n")

    return

def building_host(target):
    target.write("# Building Host\n")
    target.write("$(EXECUTABLE): $(HOST_SRCS)\n")
    target.write("\tmkdir -p $(XCLBIN)\n")
    target.write("\t$(CXX) $(CXXFLAGS) $(HOST_SRCS) -o '$@' $(LDFLAGS)\n")
    target.write("\n")

    return

def profile_report(target):
    target.write("[Debug]\n")
    target.write("profile=true\n")

    return

def mk_clean(target):
    target.write("# Cleaning stuff\n")
    target.write("RM = rm -f\n")
    target.write("RMDIR = rm -rf\n")
    target.write("clean:\n")
    target.write("\t-$(RMDIR) $(EXECUTABLE) $(XCLBIN)/{*sw_emu*,*hw_emu*} \n")
    target.write("\t-$(RMDIR) sdaccel_* TempConfig system_estimate.xtxt *.rpt\n")
    target.write("\t-$(RMDIR) src/*.ll _xocc_* .Xil emconfig.json dltmp* xmltmp* *.log *.jou *.wcfg *.wdb\n")
    target.write("\n")

    target.write("cleanall: clean\n")
    target.write("\t-$(RMDIR) $(XCLBIN)\n")
    target.write("\t-$(RMDIR) ./_x\n")
    target.write("\n")

    return

def mk_build_all(target, data):
    target.write("CP = cp -rf\n")

    args = []
    if "cmd_args" in data:
        args = data["cmd_args"].split(" ")
        if any("/data" in string for string in args):
            target.write("DATA = ./data\n")

    target.write("\n")

    target.write(".PHONY: all clean cleanall docs\n")
    target.write("all: $(EXECUTABLE) $(BINARY_CONTAINERS)\n")
    if any("/data" in string for string in args):
        target.write("\t- if test -d $(DATA); then $(CP) $(DATA) $(BUILD_DIR)/sd_card/; fi\n")
    target.write("\n")
    
    target.write(".PHONY: exe\n")
    target.write("exe: $(EXECUTABLE)\n")
    target.write("\n")

    building_kernel(target, data)
    building_host(target)

    return

def mk_check(target, data):
    target.write("check: all\n")
    target.write("ifeq ($(TARGET),$(filter $(TARGET),sw_emu hw_emu))\n")
    target.write("\temconfigutil --platform $(DEVICE) --od .\n") 
    if "em_cmd" in data:
        emu_args = data["em_cmd"].split(" ")
    target.write("\tXCL_EMULATION_MODE=$(TARGET) ./$(EXECUTABLE)")
    if emu_args:
        for arg in emu_args[1:]:
            target.write(" ")
            target.write(arg)
    target.write("\n\tsdx_analyze profile -i sdaccel_profile_summary.csv -f html\n")
    target.write("endif\n")
    target.write("\n")

    if "targets" in data:
        for mode in data["targets"]:
            target.write("#Reporting warning if not targeting for Targets\n")
            target.write("ifneq (")
            target.write(mode)
            target.write(",$(findstring ")
            target.write(mode)
            target.write(",$(TARGET)))\n")
            target.write("\t$(warning WARNING:Application supports only ")
            target.write(mode)
            target.write(" TARGET. Please use the target for running the application)\n")
            target.write("endif\n\n")

def mk_help(target):
    target.write("ECHO:= @echo\n")
    target.write("\n")
    target.write(".PHONY: help\n")
    target.write("\n")
    target.write("help::\n")
    target.write("\t$(ECHO) \"Makefile Usage:\"\n")
    target.write("\t$(ECHO) \"  make all TARGET=<sw_emu/hw_emu/hw> DEVICE=<FPGA platform>\"\n");
    target.write("\t$(ECHO) \"      Command to generate the design for specified Target and Device.\"\n")
    target.write("\t$(ECHO) \"\"\n")
    target.write("\t$(ECHO) \"  make clean \"\n");
    target.write("\t$(ECHO) \"      Command to remove the generated non-hardware files.\"\n")
    target.write("\t$(ECHO) \"\"\n")
    target.write("\t$(ECHO) \"  make cleanall\"\n")
    target.write("\t$(ECHO) \"      Command to remove all the generated files.\"\n")
    target.write("\t$(ECHO) \"\"\n")
    target.write("\t$(ECHO) \"  make check TARGET=<sw_emu/hw_emu/hw> DEVICE=<FPGA platform>\"\n");
    target.write("\t$(ECHO) \"      Command to run application in emulation.\"\n")
    target.write("\t$(ECHO) \"\"\n")
    target.write("\n")

def create_mk(target, data):
    create_params(target,data)
    add_host_flags(target, data)
    add_kernel_flags(target, data)
    add_containers(target, data)
    add_libs(target, data)
    mk_build_all(target, data)
    mk_check(target, data)
    mk_clean(target)
    mk_help(target)
    return

script, desc_file = argv
desc = open(desc_file, 'r')
data = json.load(desc)
desc.close()
target = open("Makefile", "w")

create_mk(target, data)

target.write("docs: README.md\n")
target.write("\n")

target.write("README.md: description.json\n")
target.write("\t$(ABS_COMMON_REPO)/utility/readme_gen/readme_gen.py description.json\n")
target.write("\n")

target.close

printf "Generating sdaccel.ini file for %s" %data["example"]
target = open("sdaccel.ini","w")
profile_report(target)
target.close
