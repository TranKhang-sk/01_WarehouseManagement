from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta, timezone

from logistic_nhom03 import settings
db = settings.firestore_db

def auto_assign_driver():
    now = datetime.now(timezone(timedelta(hours=7)))
    print(now)
    exports = db.collection('exports').get()
    for export in exports:
        data = export.to_dict()
        if(data['assigned_to'] == 'finding'):
            print("Đang quét đơn:", export.id)
            created = data['created_at'].astimezone(timezone(timedelta(hours=7)))
            print(created)
            print("abs:" + str(abs(now - created)))
            print("timedelta:" + str(timedelta(hours=2)))
            if abs(now - created) > timedelta(hours=2):
                print("Đơn tìm tài xế hết hạn chuyển trạng thái hủy:", export.id)
                db.collection('exports').document(export.id).update({'status' : 'canceled'})
            if abs(now - created) < timedelta(hours=2):
                print("Đơn vẫn còn trong hạn tìm tài xế:", export.id)
                deliver_ref = db.collection('users').get()
                deliver_list = []

                for doc in deliver_ref:
                    user = doc.to_dict()
                    if user.get('role') == 'deliver':
                        deliver_list.append(doc.id)
                print("Tài xế ban đầu" + str(deliver_list))

                if len(deliver_list) > 0:
                    for deliver in deliver_list:
                        exports_ref = db.collection('exports').get()
                        for item in exports_ref:
                            data1 = item.to_dict()
                            if(data1.get('assigned_to') == deliver):
                                print("Xét tài xế:" + str(deliver))
                                if(data1['status'] != 'delivering'):
                                    if(abs(data1['pickup_time'] - data['pickup_time']) < timedelta(days= 7)):
                                        deliver_list.remove(deliver)
                                        print("Xóa tài xế khỏi danh sách chờ" + str(deliver))
                if(len(deliver_list) > 0):
                    print("Danh sách tài xế cuối cùng:" + str(deliver_list))
        

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(auto_assign_driver, 'interval',seconds=20)
    scheduler.start()
