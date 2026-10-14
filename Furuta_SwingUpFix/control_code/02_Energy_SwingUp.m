function u = fcn(x,t)
%#codegen
% Torque swing-up for the supplied MJCF, phi=0 DOWN, phi=pi UP.
% Output is normalized; the actuator interface multiplies by 0.010 N*m.
% State order: [alpha; alpha_dot; phi; phi_dot], all radians / rad/s.
alpha=x(1); ad=x(2); phi=x(3); pd=x(4);
m=0.014; l=0.051; R=0.065; g=9.81;
D=8.06e-6+m*l*l;
c=m*R*l;
b=8.06e-6+m*l*l-1e-7;
a0=1.05625e-5+0.03*0.035^2+m*R^2+1e-7;
mg=m*g*l;
sp=sin(phi); cp=cos(phi);

E=0.5*D*pd*pd+mg*(1-cp);
% An empirical swing-up energy margin for this model, not a new E_up.
energyError=1.5-E/(2*mg);
% Desired arm acceleration, with continuous centering and damping.
v=-30*energyError*pd*cp-40*alpha-12*ad;
if t<0.1
    v=v+20*sin(pi*t/0.1);
end
% Soft restoring action, without replacing the energy controller.
wall=max(abs(alpha)-1.5,0);
v=v-40*sign(alpha)*wall*wall;
v=min(max(v,-150),150);

% Partial feedback linearization: arm acceleration -> actual motor torque.
% M11=a0+b*sin(phi)^2, M12=c*cos(phi), M22=D.
M11=a0+b*sp*sp; M12=c*cp;
h1=2*b*sp*cp*ad*pd-c*sp*pd*pd;
h2=-b*sp*cp*ad*ad+mg*sp ...
   +9.899130726538984e-6*pd ...
   +1.846467096315846e-5*tanh(pd/0.01);
tau=(M11-M12*M12/D)*v+h1+0.0001*ad-M12*h2/D;
tau=min(max(tau,-0.010),0.010);
u=tau/0.010;
end
