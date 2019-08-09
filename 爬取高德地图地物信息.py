# -*- coding:utf-8 -*-
# Author:Lynn
# Time:2019/8/9
# Function:矢量化郑州商城、风景名胜等范围
import json
import time
import urllib

import arcgisscripting
import arcpy
import os, random
from bs4 import BeautifulSoup

outPath = [r"D:\MyWorkSpace\商城_超级市场.shp",
           r"D:\MyWorkSpace\楼宇_住宅.shp",
           r"D:\MyWorkSpace\高尔夫_足球场.shp",
           r"D:\MyWorkSpace\风景名胜.shp",
           r"D:\MyWorkSpace\政府机关.shp",
           r"D:\MyWorkSpace\高等院校.shp",
           r"D:\MyWorkSpace\中学_小学.shp",
           ]

AMAP_API_KEY = "***" #高德地图密匙
urlParamJson = {
    'city' : '郑州',
    'output' : 'xml',
    'key' : AMAP_API_KEY,
    'types' : '',
    'citylimit' : 'true', #只返回指定城市数据
    'offset' : '20'#每页条数
}

MAX_PAGE = 100 #最大页数

class_list =[['商城', '超级市场'],
             ['楼宇', '住宅'],
             ['高尔夫球场', '足球场'],
             ['风景名胜'],
             ['政府机关'],
             ['高等院校'],
             ['中学', '小学']]


# return: list 厦门市公园POI的ID
def getParkPoiid(tps):
    poiidList = []
    for tp in tps:
        for page in range(1,MAX_PAGE) : #页数
            urlParamJson["page"] = page
            urlParamJson['types'] = tp
            print "当前 %s 页..." % page
            params = urllib.urlencode(urlParamJson)
            url = "http://restapi.amap.com/v3/place/text?%s" % params
            http = urllib.urlopen(url)
            dom = BeautifulSoup(http)
            poiList = dom.findAll("poi")
            if len(poiList)==0: #没有数据时则跳出
                break
            for poi in poiList:
                poiid = poi.id.get_text()
                poiidList.append(poiid.encode("utf8") )
                

    return poiidList


def getParkInfoList(poiidList):
    parkInfoList = []
    i = 1 #number
    for poiid in poiidList:
        parkInfo = {}
        params = urllib.urlencode({
            'id' : poiid,
            'key' : AMAP_API_KEY
        })
        url = "http://ditu.amap.com/detail/get/detail?%s" % params

        print "查询url %s" % url

        http = urllib.urlopen(url)
        jsonStr = http.read()
        park = json.loads(jsonStr)
        spec = park["data"]["spec"]  #  spec每个数据都有
        haveShp = "没有"
        if 'mining_shape' in spec.keys():
            #有 面状或线状 信息
            haveShp = "有"
            parkInfo["shape"] = spec["mining_shape"]["shape"] #保存 shape属性
            parkInfo["name"] = park["data"]["base"]["name"].encode("utf8")
            parkInfo["type"] = park["data"]["base"]["business"].encode("utf8")
            parkInfoList.append(parkInfo)
            if len(parkInfoList) % 11 == 0:
                print "已获取 %s 个矢量信息" % len(parkInfoList)

        print "%s ：%s" % (park["data"]["base"]["name"].encode("utf8"), haveShp )
        time.sleep(1)
        i = i+1
        if i%51==0:
            time.sleep(30)
    return parkInfoList

def saveParkPolygon(parkInfoList, path):
    gp = arcgisscripting.create()
    outWorkspace = os.path.split(path)[0]
    outName = os.path.split(path)[-1]
    spat_ref = "4326"
    gp.CreateFeatureClass_management(outWorkspace, outName, "POLYGON", "", "", "", spat_ref)

    gp.AddField_management(path, "name", "TEXT", field_length=250)
    gp.AddField_management(path, "type", "TEXT", field_length=250)

    cur = gp.InsertCursor(path)
    newRow = cur.newRow()
    for parkInfo in parkInfoList:
        for attr in parkInfo:
            if attr=="shape":
                # array = getXYArray(parkInfo["shape"])
                XYsStr = parkInfo["shape"]
                XYarray = gp.CreateObject("array")
                XYList = XYsStr.split(';')
                for XYstr in XYList:
                    XY = XYstr.split(',')
                    XY[0], XY[1] = float(XY[0]), float(XY[1])
                    point = gp.CreateObject("point")
                    point.X, point.Y = XY[0], XY[1]
                    XYarray.add(point)
                newRow.setValue("Shape",XYarray)
            else:
                newRow.setValue(attr, parkInfo[attr] )
        cur.InsertRow(newRow)
    del cur,newRow



if __name__ == '__main__':
    for index,tps in enumerate(class_list):
        poiidList = getParkPoiid(tps) #poid
        print "已得到 %s 个%sPOI ID" % (len(poiidList), (",").join(tps))
        parkInfoList = getParkInfoList(poiidList)
        print(parkInfoList)
        saveParkPolygon(parkInfoList, outPath[index])
