function motorTorque = fcn(u,phase,t)
%#codegen
% Torque motor, gear=1, ctrlrange=[-0.010,0.010] N*m.
% phase and t remain as ports for compatibility with the supplied model.
% Both branches use the same torque scale; balance gains were tuned for it.
u=min(max(u,-1.0),1.0);
motorTorque=0.010*u;
end
