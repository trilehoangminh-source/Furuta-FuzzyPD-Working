function setup_Furuta_SwingUpFix()
% Create/configure a separate corrected model using supported MATLAB APIs.
% Required: MATLAB/Simulink, Fuzzy Logic Toolbox, the installed mjLib blockset.
% The source V1 model is not changed. Re-running updates the generated V2.
folder=fileparts(mfilename('fullpath'));
source=fullfile(folder,'Furuta_TorqueFuzzy_V1.slx');
target=fullfile(folder,'Furuta_TorqueFuzzy_V2_Fix.slx');
xml=fullfile(folder,'furuta_simulink_torque_fixed.xml');
fisFile=fullfile(folder,'Furuta_FuzzyPD25_Clean.fis');
assert(isfile(source) && isfile(xml) && isfile(fisFile), ...
    'Giai nen toan bo goi, giu nguyen cac thu muc con.');

fisObj=readfis(fisFile);
assert(numel(fisObj.Rules)==25,'FIS phai co 25 luat.');
assignin('base','Furuta_FuzzyPD25_Clean',fisObj);
model='Furuta_TorqueFuzzy_V2_Fix';
if bdIsLoaded(model)
    assert(strcmp(get_param(model,'SimulationStatus'),'stopped'), ...
        'Hay dung mo phong truoc khi chay setup.');
elseif ~isfile(target)
    copyfile(source,target);
end
load_system(target);
modelWS=get_param(model,'ModelWorkspace');
assignin(modelWS,'Furuta_FuzzyPD25_Clean',fisObj);

plant=[model '/MuJoCo Plant'];
set_param(plant,'xmlFileRel',xml,'xmlFile',xml,'sampleTime','0.001');
assert(strcmp(char(get_param(plant,'xmlFile')),xml), ...
    'MuJoCo Plant chua tro den XML da sua.');

hybrid=[model '/Hybrid_Furuta_FuzzyPD25'];
rt=sfroot;
blocks={'02_Energy_SwingUp','04_Supervisor_Hysteresis','06_Actuator_Interface'};
for k=1:numel(blocks)
    blockPath=[hybrid '/' blocks{k}];
    chart=rt.find('-isa','Stateflow.EMChart','Path',blockPath);
    assert(numel(chart)==1,'Khong tim thay MATLAB Function: %s',blockPath);
    chart.Script=fileread(fullfile(folder,'control_code',[blocks{k} '.m']));
end

% Keep the original Mamdani FIS and every one of its 25 rules unchanged.
balance=[hybrid '/03_Balance_FuzzyPD25'];
set_param([balance '/Normalize_E'],'Gain','-1/0.2470994590080727');
set_param([balance '/Normalize_DE'],'Gain','-1/2.508255952323903');
set_param([balance '/Ku_Fuzzy'],'Gain','-2.0');
% Positive arm terms are part of the coupled upright feedback design.
set_param([balance '/Arm_Center_Kp'],'Gain','0.2828427124745972');
set_param([balance '/Arm_Damp_Kd'],'Gain','0.14609231193200561');
fisBlock=[balance '/Fuzzy_PD_25_Rules'];
set_param(fisBlock,'FIS','Furuta_FuzzyPD25_Clean', ...
    'OutputSampleNumber','101','UseLookupTable','off');
% Match the 1 ms plant step used for the separate MuJoCo verification.
set_param(model,'SolverType','Fixed-step','Solver','FixedStepDiscrete', ...
    'FixedStep','0.001','StartTime','0','StopTime','30', ...
    'LoadInitialState','off','FastRestart','off');

% Save before compiling so the patched model remains available if a local
% toolbox/blockset configuration needs attention.
save_system(model,target);
open_system(model);
try
    set_param(model,'SimulationCommand','update');
catch ME
    fprintf(2,'\nDa tao V2, nhung MATLAB chua compile thanh cong.\n');
    fprintf(2,'Hay gui nguyen van loi ben duoi de kiem tra.\n');
    rethrow(ME);
end
save_system(model,target);
fprintf('\nDA TAO: %s\n',target);
fprintf('XML: %s\n',xml);
fprintf('Gioi han tay: +/-135 deg; torque: +/-0.010 N*m; Ts=0.001 s.\n');
fprintf('Nhan Run trong model V2 de chay 30 giay.\n');
fprintf('Quy uoc: theta_rad=0 la UP; swing_mode=1 la FUZZY BALANCE.\n');
fprintf('Da kiem tra rieng bang Python/MuJoCo; MATLAB can compile/run tai may ban.\n\n');
end
