function phase = fcn(theta,pd,alpha)
%#codegen
% 0=swing-up, 1=fuzzy balance. Separate capture/release thresholds.
persistent balanced
if isempty(balanced)
    balanced=false;
end
if balanced
    if abs(theta)>0.45 || abs(pd)>5.0 || abs(alpha)>2.1
        balanced=false;
    end
else
    if abs(theta)<0.25 && abs(pd)<2.5 && abs(alpha)<1.8
        balanced=true;
    end
end
phase=double(balanced);
end
