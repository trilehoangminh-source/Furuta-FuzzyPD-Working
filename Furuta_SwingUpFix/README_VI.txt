FURUTA SWING-UP FIX
==================

CÁCH CHẠY TRONG MATLAB
1. Giải nén toàn bộ gói vào một thư mục có quyền ghi.
2. Chọn thư mục Furuta_SwingUpFix làm MATLAB Current Folder.
3. Dừng mô phỏng đang chạy, sau đó gõ:

       setup_Furuta_SwingUpFix

4. Script tạo/cấu hình và mở Furuta_TorqueFuzzy_V2_Fix.slx.
5. Nhấn Run trong model V2. Thời gian mặc định là 30 giây.
6. Xem Scope1: theta_rad cần tiến về gần 0; đây là sai lệch so với UP.
   Phi của thanh nhỏ là 0 khi DOWN, pi (hoặc -pi modulo 2*pi) khi UP.
   Cổng swing_mode có giá trị 0=SWING-UP, 1=FUZZY BALANCE.
   Dù tên là swing_mode, giá trị 1 thực tế biểu thị đang giữ thăng bằng.

CẦN CÓ
- MATLAB/Simulink, Fuzzy Logic Toolbox, MuJoCo Simulink blockset có mjLib.
- Script sử dụng Stateflow.EMChart để sửa code MATLAB Function trong model,
  cùng cơ chế mà MATLAB dùng để lưu các block MATLAB Function này.
- Model nguồn được cung cấp trong gói là V1 ông đã gửi. Script lưu bản đã
  chỉnh dưới tên V2_Fix. Lần chạy setup tiếp theo sẽ cập nhật model V2 đó.

LỖI GỐC ĐÃ XÁC NHẬN
XML gốc thiếu <compiler angle="radian"/>.
MuJoCo mặc định hiểu các góc khai báo trong MJCF theo độ. Vì vậy range
"-2.356194490192345 2.356194490192345" trở thành khoảng +/-2.356 độ,
thay vì +/-2.356 rad = +/-135 độ như bộ điều khiển đang giả định.
Tay quay đụng giới hạn trong một góc rất nhỏ, gây giật và thanh nhỏ kẹt dưới.
Giới hạn khớp MuJoCo có độ mềm, nên chuyển động có thể vượt nhẹ range.

SỬA NHỮNG GÌ
- Thêm compiler angle="radian" vào XML. Giữ giới hạn tay quay +/-135 độ,
  các thông số khối lượng/quán tính/ma sát và motor torque gear=1.
- Luật swing-up mới tạo gia tốc tay mong muốn bằng năng lượng, có kéo về
  giữa và giảm tốc liên tục. Chuyển gia tốc sang torque qua mô hình động lực.
  Biên năng lượng swing-up 1.5 là hệ số thực nghiệm cho MJCF này; năng lượng
  vật lý ở đỉnh vẫn là 2*m*g*l. Không dùng riêng energy_ratio=1 để kết luận
  thanh đã lên đỉnh khi tay quay còn đang chuyển động.
- Thay hành vi bỏ hẳn luật swing-up khi abs(alpha)>1.45 bằng tác động mềm
  bổ sung vào luật điều khiển; vẫn giữ giới hạn khớp trong XML.
- Hiệu chỉnh chuẩn hóa E, DE, gain fuzzy, phản hồi góc/vận tốc tay, và ngưỡng
  bắt/nhả cân bằng. File FIS và toàn bộ 25 luật Mamdani giữ nguyên.
- Cả hai chế độ dùng scale torque 0.010 N*m, cùng giới hạn actuator +/-0.010.
  Nhánh balance V1 trước đó dùng scale 0.008 N*m.
- Đặt bước điều khiển/plant 0.001 s và solver fixed-step discrete.

KIỂM CHỨNG ĐÃ THỰC HIỆN
Đã chạy riêng mô hình MJCF bằng Python/MuJoCo, dùng vòng điều khiển 1 ms,
giải mờ Mamdani min/min/max, centroid với 101 điểm, đúng cấu hình FIS của V1.
Đã đối chiếu ma trận quán tính và lực bias giải tích với MuJoCo.

MuJoCo 3.16.0, 6 lần chạy 30 s:
- Ban đầu đứng yên ở dưới.
- Phi ban đầu +0.05 hoặc -0.05 rad.
- Góc tay ban đầu +0.2 hoặc -0.2 rad.
- Phi=0.02 rad, alpha_dot=0.1 rad/s, phi_dot=-0.1 rad/s.
Cả 6 trường hợp bắt được đỉnh, chuyển sang balance một lần và giữ đến hết.
Bắt đầu balance sau khoảng 1.25-1.39 s. Sai lệch thanh cuối mỗi lần chạy
nằm trong khoảng +/-0.17 độ. Biên tay quay lớn nhất các lần dưới 108 độ.

MuJoCo 3.5.0, lần chạy 50 s từ đứng yên ở dưới:
- Bắt đầu balance: 1.255 s, duy trì balance đến hết 50 s.
- Góc tay lớn nhất: khoảng 98.84 độ, dưới giới hạn 135 độ.
- Sai lệch thanh lớn nhất trong 5 s cuối: khoảng 0.170 độ.
- Còn dao động nhỏ do tổ hợp fuzzy và ma sát; chưa phải hội tụ chính xác 0.

Đối chứng cùng engine, code V1 và XML gốc:
- Thanh nhỏ chỉ lệch khỏi vị trí DOWN tối đa khoảng 6.33 độ trong 30 s.
- Chỉ sửa đơn vị XML, giữ controller V1: thanh lên khoảng 118.39 độ từ DOWN,
  chưa bắt được đỉnh. Vì vậy gói này sửa cả XML lẫn bộ điều khiển.

GIỚI HẠN CỦA KIỂM CHỨNG
Chưa có MATLAB runtime trong môi trường tạo gói, nên chưa compile/run SLX
ở đây. Script setup sẽ dùng API MATLAB để tạo V2 và yêu cầu update diagram
trên máy ông, báo nguyên lỗi nếu toolbox/blockset của máy cần chỉnh thêm.
Kết quả Python/MuJoCo không xác nhận toàn bộ đường chạy Simulink. File
validate_mujoco.py tái hiện phép kiểm tra vật lý và FIS, còn setup cần được
chạy tại MATLAB. Gói dành cho mô phỏng với đúng MJCF kèm theo.

TỆP TRONG GÓI
- setup_Furuta_SwingUpFix.m : lệnh chạy đầu tiên.
- Furuta_TorqueFuzzy_V1.slx : model nguồn để script tạo bản V2.
- furuta_simulink_torque_fixed.xml : plant sửa đơn vị góc.
- Furuta_FuzzyPD25_Clean.fis : FIS 25 luật gốc.
- control_code/ : code ba MATLAB Function được script cài vào V2.
- validation/ : số liệu kiểm tra, hình so sánh, script Python chạy lại.
Không dùng file cache .slxc cũ cho bản V2; MATLAB sẽ tự tạo cache thích hợp.

THAM KHẢO API
https://mujoco.readthedocs.io/en/3.3.1/XMLreference.html#compiler
https://www.mathworks.com/help/simulink/slref/stateflow.emchart.html
