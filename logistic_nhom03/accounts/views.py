# accounts/views.py
from logistic_nhom03 import settings
from django.shortcuts import render ,redirect
from django.contrib import messages
from firebase_admin import auth, firestore
from django.http import JsonResponse
import requests
import json

db = settings.firestore_db
FIREBASE_API_KEY = "AIzaSyCgf2cpIwqhkNh0k6OBhFGDLlPGQH2Qee0"

# === GIỮ NGUYÊN HÀM CHECK ADMIN ===
def check_role_admin(request):
    try:
        if 'firebase_user' not in request.session:
            return 'login'
        
        user_id = request.session['firebase_user'].get('localId')
        user_doc = db.collection('users').document(user_id).get()

        if not user_doc.exists:
            return 'login'
        
        role = user_doc.to_dict().get('role')

        if role != 'admin':
            return 'dashboard'
            
    except Exception as e:
        return 'login'
    
    return None 


def register(request):
    redirect_to = check_role_admin(request)
    if redirect_to == 'login':
        messages.error(request, 'Bạn phải đăng nhập để thực hiện việc này.')
        return redirect('login')
    if redirect_to == 'dashboard':
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('dashboard')

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        role = request.POST.get('role', 'staff') 

        try:
            user = auth.create_user(
                email = email,
                password = password,
                display_name = name
            )
            db.collection('users').document(user.uid).set({
                'name': name,
                'email': email,
                'phone': phone,
                'role': role,
                'active': True,
                'created_at': firestore.SERVER_TIMESTAMP
            })
            messages.success(request, 'Tạo tài khoản thành công')
            return redirect('showall')
        
        except Exception as e:
            error_message = str(e)
            print(f"Register Error (Debug): {error_message}") # Chỉ in ra terminal để xem lỗi

            # === DỊCH LỖI SANG TIẾNG VIỆT ===
            if "EMAIL_EXISTS" in error_message or "EmailAlreadyExistsError" in error_message:
                messages.error(request, 'Email này đã được sử dụng bởi tài khoản khác.')
            elif "WEAK_PASSWORD" in error_message:
                 messages.error(request, 'Mật khẩu quá yếu. Vui lòng nhập ít nhất 6 ký tự.')
            elif "INVALID_EMAIL" in error_message:
                 messages.error(request, 'Địa chỉ email không đúng định dạng.')
            elif "PHONE_NUMBER_EXISTS" in error_message:
                 messages.error(request, 'Số điện thoại này đã được sử dụng.')
            else:
                # Thay vì in lỗi tiếng Anh, in câu chung chung
                messages.error(request, 'Đã xảy ra lỗi khi tạo tài khoản. Vui lòng thử lại.')
            # =================================
            
    return render(request, 'accounts/register.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            payload = json.dumps({
                "email": email,
                "password": password,
                "returnSecureToken": True
            })
            
            res = requests.post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}",
                data=payload
            )
            data = res.json()
            
            if 'idToken' in data:
                request.session['firebase_user'] = data
                if messages.get_messages(request):
                    list(messages.get_messages(request))

                user_id = request.session['firebase_user'].get('localId')
                user_doc = db.collection('users').document(user_id).get()
                
                if not user_doc.exists:
                     messages.error(request, 'Tài khoản không tồn tại trong hệ thống dữ liệu.')
                     return redirect('login')

                role = user_doc.to_dict().get('role')
                
                if role == 'staff':
                    return redirect('dashboard')
                if role == 'deliver':  
                    return redirect('deliver')
                if role == 'admin':  
                    return redirect('showall')
                
            else:
                error_message = data.get('error', {}).get('message', 'UNKNOWN_ERROR')
                print(f"Login Error (Debug): {error_message}")

                if messages.get_messages(request):
                    list(messages.get_messages(request))

                # === DỊCH LỖI ĐĂNG NHẬP ===
                if error_message == 'EMAIL_NOT_FOUND':
                    messages.error(request, 'Không tìm thấy tài khoản với email này.')
                elif error_message == 'INVALID_PASSWORD':
                    messages.error(request, 'Mật khẩu không chính xác.')
                elif error_message == 'INVALID_LOGIN_CREDENTIALS':
                    messages.error(request, 'Email hoặc mật khẩu không chính xác.')
                elif error_message == 'USER_DISABLED':
                    messages.error(request, 'Tài khoản này đã bị vô hiệu hóa.')
                elif error_message == 'TOO_MANY_ATTEMPTS_TRY_LATER':
                    messages.error(request, 'Đăng nhập sai quá nhiều lần. Vui lòng thử lại sau 5 phút.')
                else:
                    # Fallback hoàn toàn tiếng Việt
                    messages.error(request, 'Đăng nhập thất bại. Vui lòng kiểm tra lại thông tin.')

        except requests.exceptions.ConnectionError:
            messages.error(request, 'Không thể kết nối đến máy chủ. Vui lòng kiểm tra mạng.')
        except Exception as e:
            print(f"System Error (Debug): {str(e)}")
            # Ẩn lỗi tiếng Anh với người dùng
            messages.error(request, 'Đã xảy ra lỗi hệ thống. Vui lòng liên hệ quản trị viên.')
            
    return render(request, 'accounts/login.html')

def logout_view(request):
    if 'firebase_user' in request.session:
        del request.session['firebase_user']
    messages.info(request, 'Bạn đã đăng xuất thành công.')
    return redirect('login')

# === CÁC HÀM DƯỚI ĐÂY GIỮ NGUYÊN ===
def showall(request):
    redirect_to = check_role_admin(request)
    if redirect_to == 'login':
        messages.error(request, 'Bạn phải đăng nhập để thực hiện việc này.')
        return redirect('login')
    if redirect_to == 'dashboard':
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('dashboard')

    keyword = request.GET.get('q', None)
    user_ref = db.collection('users').get()
    user_list = []

    for user in user_ref:
        item = user.to_dict()
        item['id'] = user.id
        if keyword:
            keyword_lower = keyword.lower()
            name_lower = item.get('name', '').lower()
            phone_lower = item.get('phone', '').lower() 
            if keyword_lower in name_lower or keyword_lower in phone_lower:
                user_list.append(item)
        else:
            user_list.append(item) 

    context = {'users': user_list}
    return render(request, 'accounts/showall.html', context)

def delete(request, user_id):
    redirect_to = check_role_admin(request)
    if redirect_to == 'login':
        messages.error(request, 'Bạn phải đăng nhập để thực hiện việc này.')
        return redirect('login')
    if redirect_to == 'dashboard':
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('dashboard')

    if request.method == 'POST':
        db.collection('users').document(user_id).delete()
        return redirect(showall)
    
def update(request, user_id):
    redirect_to = check_role_admin(request)
    if redirect_to == 'login':
        messages.error(request, 'Bạn phải đăng nhập để thực hiện việc này.')
        return redirect('login')
    if redirect_to == 'dashboard':
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('dashboard')

    if request.method == 'POST':
        data = {}
        data['email'] = request.POST.get('email')
        data['phone'] = request.POST.get('phone')
        data['role'] = request.POST.get('role')
        data['active'] = request.POST.get('active') 
        db.collection('users').document(user_id).update(data)
        return redirect(showall)
    
    doc_ref = db.collection('users').document(user_id).get()
    user = doc_ref.to_dict()
    user['id'] = doc_ref.id
    context = {'user': user}       
    return render(request, 'accounts/update.html', context)