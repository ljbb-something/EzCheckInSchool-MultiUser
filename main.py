import json
import time
import random
import requests
import re

# 获取response.json dict
with open('./response.json', 'r', encoding='utf8')as fp:
    response_json = json.load(fp)
    college_all = response_json['data']['collegeAll']
    major_all = response_json['data']['majorAll']
    class_all = response_json['data']['classAll']

check_url = "https://reportedh5.17wanxiao.com/sass/api/epmpics"

# 输入
stus = []
tmp = input()
while tmp != 'end':
    stus.append(tmp.split(','))
    tmp = input()

# 存放网络错误时没有打卡成功的成员信息，用于重新打卡
error = []


def main():
    # 获取打卡时间信息
    now = get_time()
    if (now[0] >= 6) & (now[0] < 8):
        template_id = "clockSign1"
        customer_app_type_rule_id = 146
    elif (now[0] >= 12) & (now[0] < 14):
        template_id = "clockSign2"
        customer_app_type_rule_id = 147
    elif (now[0] >= 21) & (now[0] < 22):
        template_id = "clockSign3"
        customer_app_type_rule_id = 148
    else:
        print('未到打卡时间，将重打早间卡测试')
        template_id = "clockSign1"
        customer_app_type_rule_id = 146

    # 遍历所有需要打卡的成员
    for stu in stus:
        # 获取dept_text以及uid
        dept_text = stu[2]
        uid = stu[3]
        # 获取学院、专业和班级信息
        try:
            tmp = dept_text.split('-', 3)
            college_name = tmp[0]
            major_name = tmp[1]
            class_name = tmp[2]
        except IndexError:
            print_info_error()
            exit(1)

        # 获取deptId
        try:
            print('获取deptId中...')
            for college in college_all:
                if college['name'] == college_name:
                    college_id = college['deptId']
            for major in major_all:
                if (major['name'] == major_name) & (major['parentId'] == college_id):
                    major_id = major['deptId']
            for class_ in class_all:
                if (class_['name'] == class_name) & (class_['parentId'] == major_id):
                    class_id = class_['deptId']
                    stu.append(class_id)
            if class_id:
                print('获取deptId成功!')
        except NameError:
            print_info_error()
            exit(1)
        stu.append(template_id)
        stu.append(customer_app_type_rule_id)
        msg = check(stu)
        print(msg)
        wechat_push(uid, msg)
    # 当error list不为空时一直循环打卡 知道清空error
    while len(error) != 0:
        # 等待5min
        time.sleep(300)
        for i in range(len(error)-1, -1, -1):
            msg = check(error[i])
            print(msg)
            wechat_push(uid, msg)
            # 打卡成功后从error中删除对应成员
            if re.search('打卡成功', msg):
                del error[i]

# 获取当前时间
def get_time():
    return[(time.localtime().tm_hour + 8) % 24,
           time.localtime().tm_min,
           time.localtime().tm_sec]

# 获取随机温度
def random_temperature():
    a = random.uniform(36.2, 36.5)
    return round(a, 1)

# 打印错误信息
def print_info_error():
    """
    打印 个人信息错误
    """
    print('请检查你填写的学院、专业、班级信息！')
    print('见完美校园健康打卡页面')
    print('如 理学院-应用物理学-应物1901')

# 微信推送
def wechat_push(uid, msg):
    json = {
        "appToken": "AT_hHtOWzcFDw3nhEWfhLNJgnNDAO132pFK",
        "content": msg,
        "contentType": 1,
        "uids": [uid]
    }
    response = requests.post(
        "http://wxpusher.zjiecode.com/api/send/message", json=json)
    if response.status_code == 200:
        print('微信推送成功!')
    else:
        print('微信推送失败!')


# 打卡
def check(stu):
    stu_name = stu[0]
    stu_id = stu[1]
    dept_text = stu[2]
    class_id = stu[4]
    template_id = stu[5]
    customer_app_type_rule_id = stu[6]
    now = get_time()
    check_json = {
        "businessType": "epmpics",
        "method": "submitUpInfoSchool",
        "jsonData": {
            "deptStr": {
                "deptid": class_id,
                "text": dept_text
            },
            "areaStr": {
                "streetNumber": "", "street": "长椿路辅路", "district": "中原区", "city": "郑州市", "province": "河南省",
                "town": "", "pois": "河南工业大学(莲花街校区)", "lng": 113.544407 + random.random() / 10000,
                "lat": 34.831014 + random.random() / 10000, "address": "中原区长椿路辅路河南工业大学(莲花街校区)",
                "text": "河南省-郑州市", "code": ""
            },
            "reportdate": round(time.time() * 1000),
            "customerid": 43,
            "deptid": class_id,
            "source": "app",
            "templateid": template_id,
            "stuNo": stu_id,
            "username": stu_name,
            "userid": round(time.time()),
            "updatainfo": [
                {
                    "propertyname": "temperature",
                    "value": random_temperature()
                },
                {
                    "propertyname": "symptom",
                    "value": "无症状"
                }
            ],
            "customerAppTypeRuleId": customer_app_type_rule_id,
            "clockState": 0
        },
    }
    flag = 0
    for i in range(1, 2):
        print('{0}第{1}次尝试打卡中...'.format(stu_name, i))
        response = requests.post(check_url, json=check_json)
        if response.status_code == 200:
            flag = 1
            break
        else:
            print('{0}第{1}次打卡失败!30s后重新打卡'.format(stu_name, i))
            time.sleep(30)
    print(response.text)
    time_msg = str(now[0]) + '时' + str(now[1]) + '分' + str(now[2]) + '秒'
    if flag == 1:
        if response.json()["msg"] == '成功':
            msg = time_msg + '时' + stu_name + "打卡成功"
        else:
            msg = time_msg + "打卡异常"
    else:
        msg = time_msg + "网络错误打卡失败!5min后重新打卡!"
        error.append(stu)
    return msg


if __name__ == "__main__":
    main()