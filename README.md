# Furuta-FuzzyPD-Working
# Furuta Rotary Inverted Pendulum — Energy Swing-up + Fuzzy-PD

Mã nguồn mô phỏng **con lắc ngược quay (Furuta pendulum)** bằng **MATLAB/Simulink + MuJoCo**. Bộ điều khiển gồm hai giai đoạn:

- **Swing-up:** đưa con lắc từ vị trí dưới lên gần vị trí thẳng đứng.
- **Balance:** dùng **Fuzzy-PD 25 luật** để giữ con lắc gần vị trí thẳng đứng.

> **Bản lưu nhóm:** phiên bản `Furuta_TorqueFuzzy_V2_Fix.slx` đã được chạy thành công trên máy phát triển ngày 14/10/2026. Cần kiểm tra lại khi chạy trên máy khác. Đây là mô phỏng nghiên cứu, **không phải bộ điều khiển an toàn cho phần cứng thật**.

## 1. Cấu trúc dự án

```text
Furuta-FuzzyPD-Working/
├── Furuta_TorqueFuzzy_V2_Fix.slx      # Mô hình Simulink đang dùng
├── Furuta_FuzzyPD25_Clean.fis        # Bộ luật Fuzzy-PD (25 luật)
├── furuta_simulink_torque_fixed.xml  # Động lực học + torque actuator của MuJoCo
├── setup_Furuta_SwingUpFix.m         # Script thiết lập môi trường mô hình
├── control_code/                     # Mã các bộ điều khiển (nếu có)
├── validation/                       # Script và kết quả kiểm tra (nếu có)
├── README_VI.txt                     # Ghi chú bổ sung (nếu có)
└── README.md                         # Hướng dẫn này
```

**Quan trọng:** Dùng đúng bộ ba `.slx`, `.fis`, `.xml` nêu trên. **Không chạy nhầm** `Furuta_TorqueFuzzy_V1.slx` hay XML position-actuator cũ.

Nếu mô hình có tham chiếu tới `furuta_generated.xml` hoặc một file khác ngoài thư mục này, hãy bổ sung file đó vào repository và chỉnh lại đường dẫn trước khi chia sẻ cho nhóm.

## 2. Phần mềm và thư viện cần cài

### Bắt buộc để chạy Simulink

| Thành phần | Ghi chú |
|---|---|
| **MATLAB R2025a** | Phiên bản đã dùng để phát triển; phiên bản khác cần tự kiểm tra tương thích |
| **Simulink** | Mở/chạy file `.slx` |
| **Fuzzy Logic Toolbox** | Đọc `.fis` và chạy khối Fuzzy Logic Controller |
| **[MuJoCo–Simulink Blockset](https://github.com/mathworks-robotics/mujoco-simulink-blockset)** | Cung cấp khối `MuJoCo Plant` |
| **C/C++ compiler được MATLAB hỗ trợ** | Cần khi build blockset trên Windows; có thể dùng Visual Studio 2022 C++ Build Tools |

Tham khảo hướng dẫn cài đặt và build chính thức của blockset ở repository liên kết phía trên.

### Tùy chọn (không bắt buộc nếu chỉ chạy `.slx`)

- **Python + `mujoco`**: dùng cho các script Python trực quan hóa/kiểm tra trạng thái MuJoCo, nếu thành viên muốn chạy chúng.
- **Git**: dùng để tải dự án và lưu lịch sử thay đổi.

**Không cần cài PyTorch/SAC chỉ để chạy bộ Fuzzy-PD hiện tại.**

## 3. Tải source từ GitHub

```powershell
git clone https://github.com/USERNAME/Furuta-FuzzyPD-Working.git
cd Furuta-FuzzyPD-Working
```

Thay `USERNAME` bằng tài khoản chủ repository. Nếu repository để **Private**, chủ repo phải mời thành viên vào **Settings → Collaborators**.

## 4. Cài MuJoCo–Simulink Blockset (chỉ làm lần đầu trên mỗi máy)

1. Tải hoặc clone [mathworks-robotics/mujoco-simulink-blockset](https://github.com/mathworks-robotics/mujoco-simulink-blockset).
2. Cài **Visual Studio 2022 Build Tools** với thành phần **Desktop development with C++** nếu chưa có compiler.
3. Mở MATLAB, chọn **Current Folder** là thư mục gốc của blockset.
4. Trong MATLAB Command Window, chạy lần lượt:

```matlab
install
cd tools
setupBuild
mex -setup c++
build
```

5. Sau khi build thành công, thử ví dụ từ blockset:

```matlab
mj_gettingStarted
```

> Nếu blockset đã được cài và build trước đó, bỏ qua mục này. Nếu các bước trên khác phiên bản blockset đang dùng, làm theo **README của chính blockset**.

## 5. Chạy mô phỏng Furuta

1. Mở **MATLAB R2025a**.
2. Chọn **Current Folder** là thư mục chứa `Furuta_TorqueFuzzy_V2_Fix.slx`.
3. Chạy script thiết lập (có sẵn trong project):

```matlab
setup_Furuta_SwingUpFix
```

4. Nếu script chưa tự mở mô hình, chạy:

```matlab
open_system('Furuta_TorqueFuzzy_V2_Fix.slx')
```

5. Nhấp đôi vào khối **MuJoCo Plant** và **kiểm tra file MJCF/XML** được chọn là:

```text
furuta_simulink_torque_fixed.xml
```

   Đường dẫn XML có thể đang là đường dẫn tuyệt đối của máy đã tạo mô hình. Trên máy khác, cần chọn lại XML phù hợp rồi lưu bản sao của mô hình.

6. Kiểm tra bộ Fuzzy được nạp đúng:

```matlab
fis = readfis('Furuta_FuzzyPD25_Clean.fis');
numel(fis.Rules)  % Kết quả mong đợi: 25
```

7. Trong Simulink, chọn **Normal** mode. Chạy thử **2–5 giây** để kiểm tra lỗi, sau đó tăng **Stop Time lên 30–50 giây** nếu không có bất thường.

### Lưu ý quan trọng về XML

- Bản đang chạy dùng **torque actuator**, tín hiệu điều khiển có đơn vị **N·m**, không phải góc đặt motor (rad).
- XML cần diễn giải giới hạn góc đúng đơn vị. Ở bản sửa thành công đã sử dụng cấu hình `compiler angle="radian"`; hãy kiểm tra thuộc tính này trong XML nếu có giới hạn khớp khai báo bằng radian.
- Không ghép controller xuất mô-men với XML sử dụng `<position>` actuator.

## 6. Dấu hiệu mô phỏng chạy đúng

Theo kết quả chạy trên máy phát triển (ngày 14/10/2026):

| Tín hiệu | Kỳ vọng khi chạy đúng |
|---|---|
| `swing_mode` | Ban đầu **0** (swing-up), sau đó chuyển thành **1** (balance) và duy trì |
| Góc con lắc | Tiến đến vùng thẳng đứng và duy trì gần vị trí cân bằng (đối chiếu quy ước góc trong model) |
| `phi_dot` | Giảm về gần **0 rad/s** trong giai đoạn balance |
| Góc cánh tay `alpha` | Dao động hữu hạn, không mắc ở giới hạn khớp |
| `motor_torque_Nm` | Có tín hiệu mô-men tương ứng với lệnh điều khiển |

Trong lần chạy đã báo cáo, thời điểm chuyển sang balance khoảng **1,26 giây**. Đây là **mốc tham khảo của một cấu hình**, không phải thời gian bảo đảm trên mọi máy/thay đổi mô hình.

## 7. Khắc phục lỗi thường gặp

| Lỗi | Cách kiểm tra |
|---|---|
| `Unrecognized function or variable 'Furuta_FuzzyPD25_Clean'` | Chạy lại `setup_Furuta_SwingUpFix`; kiểm tra FIS được nạp vào Base/Model Workspace |
| Không tìm thấy `MuJoCo Plant` hoặc S-Function | Kiểm tra cài đặt, MATLAB path và bước build MuJoCo–Simulink Blockset |
| Không tìm thấy XML | Mở Block Parameters của `MuJoCo Plant`, chọn lại file `furuta_simulink_torque_fixed.xml` |
| Con lắc giật, không swing-up | Kiểm tra XML/đơn vị góc, actuator loại torque, compiler và đúng bản `.slx`; chưa vội đổi gains |
| Model có cảnh báo đường dẫn `C:\...` | Máy mới đang dùng đường dẫn cũ; sửa bằng đường dẫn mới trên máy đó |

## 8. Cách làm việc nhóm an toàn

**Giữ nguyên bản chạy được trước khi thử thuật toán mới.** Mỗi lần chỉnh sửa:

```powershell
git status
git add .
git commit -m "Describe changes"
git push
```

Nên tạo nhánh riêng để thử nghiệm:

```powershell
git switch -c experiment/neural-controller
```

Không commit thư mục `.venv/`, `slprj/`, cache `.slxc` hoặc file có thông tin đăng nhập.

Khi đã lưu bản đầu tiên, nên gắn tag Git, ví dụ `v1.0-fuzzy-working`, để cả nhóm quay lại bản ổn định khi cần.

## 9. Nguồn tham khảo

- S.-E. Oltean (2014), *Swing-up and stabilization of the rotational inverted pendulum using PD and fuzzy-PD controllers*, Procedia Technology 12, 57–64.
- R. Agrawal và R. Mitra (2013), *Adaptive Neuro Fuzzy Inference Structure Controller for Rotary Inverted Pendulum*.
- [MathWorks Robotics — MuJoCo–Simulink Blockset](https://github.com/mathworks-robotics/mujoco-simulink-blockset).

---

**Ghi chú cho nhóm:** File README được biên soạn theo tên file và kết quả mô phỏng đã chia sẻ. Trước khi coi hướng dẫn là hoàn toàn tái lập được trên máy mới, nhóm nên kiểm tra thực tế nội dung `setup_Furuta_SwingUpFix.m`, đường dẫn XML và các thư viện phụ thuộc của mô hình V2.
