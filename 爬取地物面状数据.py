# -*- coding:utf-8 -*-
# Author:PasserQi
# Time:2017/9/29
# Function:矢量化厦门市公园范围
import json
import time
import urllib
import requests
import os, shapefile
from bs4 import BeautifulSoup

outPath = r"D:\MyWorkSpace\郑州"

AMAP_API_KEY = "***" #高德地图密匙
urlParamJson = {
    'city' : '郑州',
    'output' : 'xml',
    'key' : AMAP_API_KEY,
    'types' : '公园',
    'citylimit' : 'true', #只返回指定城市数据
    'offset' : '20'#每页条数
}

class_list =[['公园', '广场'],
             ['商城', '超级市场'],
             ['楼宇', '住宅'],
             ['高尔夫球场', '足球场'],
             ['风景名胜'],
             ['政府机关'],
             ['高等院校'],
             ['中学', '小学']]

MAX_PAGE = 100 #最大页数

# return: list 郑州市公园POI的ID
def getPoiid(type_list):

    poiidList = []
    for tp in type_list:
        for page in range(1,MAX_PAGE) : #页数
            urlParamJson['types'] = tp
            urlParamJson["page"] = page
            print("当前 %s 页..." % page)
            params = urllib.parse.urlencode(urlParamJson)
            url = "http://restapi.amap.com/v3/place/text?%s" % params
            print(url)
            http = requests.get(url)
            dom = BeautifulSoup(http.content)
            poiList = dom.findAll("poi")
            if len(poiList)==0: #没有数据时则跳出
                break
            for poi in poiList:
                poiid = poi.id.get_text()
                poiidList.append(poiid.encode("utf8") )
            
    return poiidList


def getInfoList(poiidList):
    parkInfoList = []
    i = 1 #number
    for poiid in poiidList:
        parkInfo = {}
        params = urllib.parse.urlencode({
            'id' : poiid,
            'key' : AMAP_API_KEY
        })
        url = "http://ditu.amap.com/detail/get/detail?%s" % params

        print("查询url %s" % url)

        http = requests.get(url)
        jsonStr = http.content
        park = json.loads(jsonStr)
        #print(park)
        spec = park["data"]["spec"] #spec每个数据都有
        haveShp = "没有"
        for key in spec:
            if key=="mining_shape":  #有 面状或线状 信息
                haveShp = "有"
                parkInfo["shape"] = [location.split(",") for location in spec[key]["shape"].split(";")] #保存 shape属性
                parkInfo["name"] = park["data"]["base"]["name"].encode("utf8")
                parkInfo["type"] = park["data"]["base"]["business"].encode("utf8")
                parkInfoList.append(parkInfo)

                if len(parkInfoList) % 11 == 0:
                    print("已获取 %s 个公园的矢量信息" % len(parkInfoList))

            break
        print("%s ：%s" % (park["data"]["base"]["name"].encode("utf8"), haveShp ))
        time.sleep(1)
        i = i+1
        if i%51==0:
            time.sleep(60)
    
    return parkInfoList


if __name__ == '__main__':
    polygon = shapefile.Writer(outPath, shapeType=shapefile.POLYGON)
    for type_list in class_list:
        poiidList = getPoiid(type_list) #得到公园id
        print("已得到 %s {} POI ID".format(type_list, len(poiidList)) , poiidList)
        parkInfoList = getInfoList(poiidList)
        parkInfoList = [[[float(num) for num in nums] for nums in location['shape']] for location in parkInfoList]
        print("获取到全部的{} {} 条信息".format(type_list, len(parkInfoList)))
        field_name = (",").join(type_list)
        polygon.poly(parkInfoList)
        polygon.field(field_name, 'C')
        polygon.record(name=field_name)
    
    polygon.close()
