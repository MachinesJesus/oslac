"""
Test AirCon Contoller
This py file is intended to test control of the solar following air conditioner.
Author: CR
Date Created: 05/07/17

Log:
2018-05-08: Adding the RPi GPIO code
"""


import database
import sunspecModbus
import configuration



# Multithreading support so can stop acquistion softly
import threading
import signal
import math
import datetime
import sys
import time # For sleep

from pyModbusTCP.client import ModbusClient

from enum import Enum


#RPI IMPORTS

import datetime
from time import sleep
from gpiozero import LED
from time import sleep


class sac_control(object):
    """RPI solar controller output config"""    
    def __init__(self):
        self.state = 0
        self.drm1 = LED(17)
        self.drm2 = LED(27)
        self.drm3 = LED(22)   
        self.drm1.off()
        self.drm2.off()
        self.drm3.off()

    def set_output(self):
        if self.state==1:
            self.drm1.on()
        elif self.state==2:
            self.drm2.on()
        elif self.state==3:
            self.drm3.on()
        else:
            self.drm1.off()
            self.drm2.off()
            self.drm3.off()
            

class ErrorLevels(Enum):
    FATAL   = 1
    ERROR   = 2
    NOTICE  = 3
    DEBUG   = 4

class Device(Enum):
    INVERTER     = 1
    METER        = 2


import ctypes
# import time

import configuration

'''
 These classes/structures/unions, allow easy conversion between
 modbus 16bit registers and ctypes (a useful format)
'''


# Single register (16 bit) based types
class convert1(ctypes.Union):
    _fields_ = [("u16", ctypes.c_uint16),
                ("s16", ctypes.c_int16)]


# Two register (32 bit) based types
class x2u16Struct(ctypes.Structure):
    _fields_ = [("h", ctypes.c_uint16),
                ("l", ctypes.c_uint16)]


class convert2(ctypes.Union):
    _fields_ = [("float", ctypes.c_float),
                ("u16", x2u16Struct),
                ("sint32", ctypes.c_int32),
                ("uint32", ctypes.c_uint32)]


# Four register (64 bit) based types
class x4u16Struct(ctypes.Structure):
    _fields_ = [("hh", ctypes.c_uint16),
                ("hl", ctypes.c_uint16),
                ("lh", ctypes.c_uint16),
                ("ll", ctypes.c_uint16)]


class convert4(ctypes.Union):
    _fields_ = [("u16", x4u16Struct),
                ("sint64", ctypes.c_int64),
                ("uint64", ctypes.c_uint64)]



"""
@brief:        Checks if there was an error during datacollection
@detail:        Checks if there was an error during data collection,
                and if there was an error, log it.
@created:      18th Feb 2017
@param:        Device
@param:        String containing called function
@return:        Flase when no error
                True when error
"""
def errorModbus(modbusDevice, function):
    if modbusDevice == Device.INVERTER:
        errorNo=sunspecModbus.inv_lastError()
    elif modbusDevice == Device.METER:
        errorNo=sunspecModbus.mtr_lastError()
    else:
        return(-1)
    if errorNo != 0:
        database.logMsg(ErrorLevels.ERROR.value,str(function)+" failure")
        #print("** There was an error when using function "+str(function))
        return True
    else:
        return False


"""
@brief:        Instantanious AC Voltage at Feed-in Point [Volts] via Smart Meter
@detail:       For three-phase, this is average phase-to-neutral voltage
@created:      14th Feb 2017
@return:       Instantanious AC Voltage (float32)
"""
def mtr_ACVoltageAverage_V():
    regs = mb_meter.read_holding_registers(40080-1, 2)
    Translate=convert2()
    Translate.u16.h = regs[1]
    Translate.u16.l = regs[0]
    return Translate.float
    #print("Feed-in AC Voltage="+str(Translate.float))

"""
@brief:        Instantanious Total AC Power at Feed-in Point [Watts] via Smart Meter
@detail:       For three-phase, this is sum of all phases
               Positive is inwards (from grid), negative is outwards (to grid)
@created:      14th Feb 2017
@return:       Instantanious AC Power (float32)
"""
def mtr_ACPowerTotal_W():
    regs = mb_meter.read_holding_registers(40098-1, 2)
    Translate=convert2()
    Translate.u16.h = regs[1]
    Translate.u16.l = regs[0]
    return Translate.float
    #print("Feed-in AC Power="+str(Translate.float))

"""
@brief:        Instantanious Site Power [Watts] from Inverter
@created:      13th Feb 2017
@return:       Current Site Power (uint32)
"""
def inv_SitePower_W():
    regs = mb_inverter.read_holding_registers(500-1, 2)
    Translate=convert2()
    Translate.u16.h = regs[1]
    Translate.u16.l = regs[0]
    return Translate.uint32
    #print("Site Power="+str(Translate.uint32))


class RERSolarAc(object):
    def __init__(self):
        self.time_step = 10
        self.P_rated = 2500.0
        self.P_000 = 0.0
        self.P_050 = 0.5*self.P_rated
        self.P_075 = 0.75*self.P_rated
        self.P_100 = self.P_rated
        self.state = '000' #others 050, 075, 100
        self.D0 = 1
        self.D1 = 0
        self.D2 = 0
        self.Priority = 0 # 0 is no ohm pilot / ac lower prio, 1 overrides ohm pilot
        self.P_inv = 0.0
        self.P_meter = 0.0
        self.P_excess = 0.0
        self.P_load = 0.0
        self.P_thres0 = 50.0
        self.P_thres50 = 1300.0

    def get_solar_data(self):
        self.P_inv = inv_SitePower_W()
        self.P_meter = mtr_ACPowerTotal_W()
        self.P_load = self.P_inv + self.P_meter
        #print("Inverter = %f W; Meter = %f W" % (self.P_inv, self.P_meter))

    def calc_control(self):

        # Decide on what input data to use
        if self.Priority == 0:
            self.P_excess = -1.0*self.P_meter
            #print('Priority 0: meter excess follow')

            # State machine for the progression of power levels
            if self.state == '000':
                if self.P_excess > 0.5 * self.P_rated:
                    self.state = '050'
            elif self.state == '050':
                if self.P_excess > 0.25 * self.P_rated:
                    self.state = '075'
                if self.P_excess < self.P_thres0:
                    self.state = '000'
            elif self.state == '075':
                if self.P_excess > 0.25 * self.P_rated:
                    self.state = '100'
                if self.P_excess < self.P_thres0:
                    self.state = '000'
            elif self.state == '100':
                if self.P_excess < self.P_thres0:
                    self.state = '000'
                elif self.P_excess < self.P_thres50:
                    self.state = '050'

        else:
            self.P_excess = self.P_inv
            print('Priority 1: direct inverter follow')

            if self.P_excess > self.P_rated:
                self.state = '100'
            elif self.P_excess > 0.75 * self.P_rated:
                self.state = '075'
            elif self.P_excess > 0.5 * self.P_rated:
                self.state = '050'
            else:
                self.state = '000'



        #Now process the DIO outputs
        # if self.P_excess > self.P_100:
        #     self.state = '100'
        #     self.D0 = 0
        #     self.D1 = 0
        #     self.D2 = 0
        #
        # elif self.P_excess > self.P_075:
        #     self.state = '075'
        #     self.D0 = 0
        #     self.D1 = 0
        #     self.D2 = 1
        # elif self.P_excess > self.P_050:
        #     self.state = '050'
        #     self.D0 = 0
        #     self.D1 = 1
        #     self.D2 = 0
        # else:
        #     self.state = '000'
        #     self.D0 = 1
        #     self.D1 = 0
        #     self.D2 = 0

        print('state is %s; and Load %f W; Inverter %f W; Meter %f W' % (self.state, self.P_load,
                                                                                self.P_inv, self.P_meter))

        #Set Rpi GPIOs
        #GPIOx=D0
        #GPIOx=D1
        #GPIOx=D2

    def run_loop(self):
        self.get_solar_data()
        self.calc_control()
        time.sleep(self.time_step)


if __name__ == "__main__":

    #run as cron job delay for startup
    sleep(60)
    
    solar_ac_ob = RERSolarAc()

    mb_inverter = ModbusClient(host=configuration.INVERTER_IP, port=configuration.MODBUS_PORT, auto_open=True,
                               auto_close=True, timeout=configuration.MODBUS_TIMEOUT,
                               unit_id=1)  # As directly connecting to inverter, its addr is 0 #CR UNIT ID=1 in AU

    mb_meter = ModbusClient(host=configuration.INVERTER_IP, port=configuration.MODBUS_PORT, auto_open=True,
                            auto_close=True, timeout=configuration.MODBUS_TIMEOUT,
                            unit_id=configuration.METER_ADDR)  # Smart Meter unit ID (device addr) is 240

    #for x in range(20):
        #solar_ac_ob.run_loop()
    
    sac_ob = sac_control()
    sleep(3)
    
    loops=8
    deadtime=1
    
    restartdelaytime=300
    statetime3=60
    statetime2=50
    statetime1=60
    endlooptime=30

    
    #for i in range(loops):
    while(True):
        
        try:
            solar_ac_ob.run_loop()
            print(int(sac_ob.drm1.value), int(sac_ob.drm2.value), int(sac_ob.drm3.value))
        except:
            print("No inverter TCP connection")
            
        try:
            now_time = datetime.datetime.now()
            #add cloud write here, if you want to record data to cloud service.
        except:
            print("Time or cloud write failure.")
        
        if solar_ac_ob.P_meter > -50.0:
            print ("DRM1 as P(meter)=%f" %solar_ac_ob.P_meter)
            #0%
            sac_ob.drm1.on()
            sleep(statetime1)
            sac_ob.drm1.off()
            sleep(deadtime)
            try:
                solar_ac_ob.run_loop()
            except:
                print("No inverter TCP connection")
            sleep(restartdelaytime)
            
        sleep(endlooptime)
                



