import json
import time
import random
import requests

# 获取response.json dict
with open('./response.json', 'r', encoding='utf8')as fp:
    response_json = json.load(fp)
    college_all = response_json['data']['collegeAll']
    major_all = response_json['data']['majorAll']
    class_all = response_json['data']['classAll']

# 输入Secrets
stu_names = input().split(',')
stu_ids = input().split(',')
dept_texts = input().split(',')
uids = input().split(',')


def main():
    """
    主函数
    """
    for j in range(len(dept_texts)):
        stu_name = stu_names[j]
        stu_id = stu_ids[j]
        dept_text = dept_texts[j]
        uid = uids[j]
        # 获取学院、专业和班级信息
        try:
            info = dept_text.split('-', 3)
            college_name = info[0]
            major_name = info[1]
            class_name = info[2]
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
            if class_id:
                print('获取deptId成功!')
        except NameError:
            print_info_error()
            exit(1)

        # 时间判断 Github Actions采用国际标准时
        time_h = (time.localtime().tm_hour + 8) % 24
        time_m = time.localtime().tm_min
        time_s = time.localtime().tm_sec
        if (time_h >= 6) & (time_h < 8):
            template_id = "clockSign1"
            customer_app_type_rule_id = 146
        elif (time_h >= 12) & (time_h < 14):
            template_id = "clockSign2"
            customer_app_type_rule_id = 147
        elif (time_h >= 21) & (time_h <= 22):
            template_id = "clockSign3"
            customer_app_type_rule_id = 148
        else:
            print("现在是%d点%d分，将打卡早间档测试" % (time_h, time_m))
            template_id = "clockSign1"
            customer_app_type_rule_id = 146

        # 随机温度(36.2~36.5)
        a = random.uniform(36.2, 36.5)
        temperature = round(a, 1)

        check_url = "https://reportedh5.17wanxiao.com/sass/api/epmpics"

        check_json = {
            "businessType": "epmpics",
            "method": "submitUpInfoSchool",
            "jsonData": {
                "deptStr": {
                    "deptid": class_id,
                    "text": dept_text
                },
                "areaStr": {"streetNumber": "", "street": "长椿路辅路", "district": "中原区", "city": "郑州市", "province": "河南省",
                            "town": "", "pois": "河南工业大学(莲花街校区)", "lng": 113.544407 + random.random() / 10000,
                            "lat": 34.831014 + random.random() / 10000, "address": "中原区长椿路辅路河南工业大学(莲花街校区)",
                            "text": "河南省-郑州市", "code": ""},
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
                        "value": temperature
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

        # 提交打卡与结果判定
        flag = 0
        for i in range(1, 5):
            print('成员{0}第{1}次尝试打卡中...'.format(j+1, i))
            response = requests.post(check_url, json=check_json)
            if response.status_code == 200:
                flag = 1
                break
            else:
                print('成员{0}第{1}次打卡失败!'.format(j+1, i))
                time.sleep(60)
        print(response.text)
        time_msg = str(time_h) + '时' + str(time_m) + '分' + str(time_s) + '秒'
        if flag == 1:
            if response.json()["msg"] == '成功':
                msg = time_msg + '时' + stu_name + "打卡成功"
            else:
                msg = time_msg + "打卡异常"
        else:
            msg = time_msg + "网络错误打卡失败"

        print(msg)
        # 微信通知
        wechat_push(uid, msg)


def wechat_push(uid, msg):
    json = {
        "appToken": "AT_hHtOWzcFDw3nhEWfhLNJgnNDAO132pFK",
        "content": msg,
        "contentType": 1,
        "uids": [
            uid
        ]
    }
    response = requests.post("http://wxpusher.zjiecode.com/api/send/message", json=json)
    if response.status_code == 200:
        print('微信推送成功!')
    else:
        print('微信推送失败!')


def print_info_error():
    """
    打印 个人信息错误
    """
    print('请检查你填写的学院、专业、班级信息！')
    print('见完美校园健康打卡页面')
    print('如 理学院-应用物理学-应物1901')


if __name__ == '__main__':
    main()
