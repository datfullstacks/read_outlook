# read_outlook

Hệ thống web nhỏ để đọc Hotmail/Outlook bằng **Microsoft Graph API + OAuth2 refresh token**, thiết kế để deploy được cả local và **Vercel**.

## Tính năng
- Nhập nhiều tài khoản theo định dạng: `email|password|refresh_token|client_id`.
- Dùng refresh token để lấy access token mới từ Microsoft.
- Đọc 10 email gần nhất qua Graph API (`/me/messages`).
- Hiển thị tiêu đề, người gửi, thời gian nhận và nội dung preview.

## Chạy local
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export MS_TENANT=common
# Nếu app Azure yêu cầu secret thì set thêm biến sau:
# export MS_CLIENT_SECRET=your_client_secret
python app.py
```

Mở: `http://127.0.0.1:5000`

## Deploy lên Vercel
Repo đã có sẵn `vercel.json` để chạy Flask bằng runtime Python của Vercel.

### 1) Chuẩn bị
- Push code lên GitHub/GitLab/Bitbucket.
- Import project vào Vercel.

### 2) Cấu hình biến môi trường trên Vercel
Trong **Project Settings → Environment Variables** thêm:
- `MS_TENANT` (ví dụ `common` hoặc tenant id cụ thể)
- `MS_CLIENT_SECRET` (nếu app Azure yêu cầu confidential client)

## `MS_TENANT` lấy ở đâu?

Bạn có 3 cách cấu hình, tùy mục tiêu đăng nhập:

1. `common`  
   - Cho phép cả tài khoản Microsoft cá nhân + tổ chức (đa tenant).
   - Dùng nhanh khi test.

2. `organizations` hoặc `consumers`  
   - `organizations`: chỉ tài khoản công ty/trường học (Azure AD/Entra ID).
   - `consumers`: chỉ tài khoản cá nhân Outlook/Hotmail.

3. Tenant ID cụ thể (khuyến nghị production)  
   - Vào **Azure Portal → Microsoft Entra ID → Overview → Tenant ID**.
   - Copy giá trị GUID (ví dụ: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`) và gán cho `MS_TENANT`.
   - Khi cố định tenant ID, app chỉ chấp nhận token thuộc tenant đó (an toàn hơn).

Ví dụ local:
```bash
export MS_TENANT=common
# hoặc
export MS_TENANT=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### 3) Deploy
- Vercel sẽ tự đọc `requirements.txt` và `vercel.json`.
- Sau khi deploy xong, truy cập domain Vercel để dùng UI.

## Lưu ý bảo mật
- Không lưu refresh token thật vào git.
- Trường `password` hiện chỉ để tương thích định dạng đầu vào, không dùng trong luồng Graph API OAuth2.
- Nên triển khai thêm mã hóa token, xác thực truy cập và rate limit trước khi dùng production.
