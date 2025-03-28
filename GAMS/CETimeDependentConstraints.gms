Sets
	block0h(h)
	block1h(h)
	blockpeaknet2h(h)
	blockpeaktotal3h(h)
	block4h(h)
	blockpeaknetramp5h(h)
	block6h(h)
	;

Parameters
	pWeightblock0h
	pWeightblock1h
	pWeightblockpeaknet2h
	pWeightblockpeaktotal3h
	pWeightblock4h
	pWeightblockpeaknetramp5h
	pWeightblock6h
	pInitSOC(storageegu)
	pInitSOCtech(storagetech)
	pHourInitblock0h
	pHourFinalblock0h
	pHourInitblock1h
	pHourFinalblock1h
	pHourInitblockpeaknet2h
	pHourFinalblockpeaknet2h
	pHourInitblockpeaktotal3h
	pHourFinalblockpeaktotal3h
	pHourInitblock4h
	pHourFinalblock4h
	pHourInitblockpeaknetramp5h
	pHourFinalblockpeaknetramp5h
	pHourInitblock6h
	pHourFinalblock6h
	pMaxgenhydroblock0h(z)
	pMaxgenhydroblock1h(z)
	pMaxgenhydroblockpeaknet2h(z)
	pMaxgenhydroblockpeaktotal3h(z)
	pMaxgenhydroblock4h(z)
	pMaxgenhydroblockpeaknetramp5h(z)
	pMaxgenhydroblock6h(z)
	;

$if not set gdxincname $abort 'no include file name for data file provided'
$gdxin %gdxincname%
$load block0h,block1h,blockpeaknet2h,blockpeaktotal3h,block4h,blockpeaknetramp5h,block6h
$load pWeightblock0h,pWeightblock1h,pWeightblockpeaknet2h,pWeightblockpeaktotal3h,pWeightblock4h,pWeightblockpeaknetramp5h,pWeightblock6h
$load pInitSOC,pInitSOCtech
$load pMaxgenhydroblock0h,pMaxgenhydroblock1h,pMaxgenhydroblockpeaknet2h,pMaxgenhydroblockpeaktotal3h,pMaxgenhydroblock4h,pMaxgenhydroblockpeaknetramp5h,pMaxgenhydroblock6h
$gdxin

pHourInitblock0h = smin(h$block0h(h),ord(h));
pHourFinalblock0h = smax(h$block0h(h),ord(h));
pHourInitblock1h = smin(h$block1h(h),ord(h));
pHourFinalblock1h = smax(h$block1h(h),ord(h));
pHourInitblockpeaknet2h = smin(h$blockpeaknet2h(h),ord(h));
pHourFinalblockpeaknet2h = smax(h$blockpeaknet2h(h),ord(h));
pHourInitblockpeaktotal3h = smin(h$blockpeaktotal3h(h),ord(h));
pHourFinalblockpeaktotal3h = smax(h$blockpeaktotal3h(h),ord(h));
pHourInitblock4h = smin(h$block4h(h),ord(h));
pHourFinalblock4h = smax(h$block4h(h),ord(h));
pHourInitblockpeaknetramp5h = smin(h$blockpeaknetramp5h(h),ord(h));
pHourFinalblockpeaknetramp5h = smax(h$blockpeaknetramp5h(h),ord(h));
pHourInitblock6h = smin(h$block6h(h),ord(h));
pHourFinalblock6h = smax(h$block6h(h),ord(h));

nonInitH(h)= yes;
nonInitH(h)$[ord(h)=pHourInitblock0h] = no;
nonInitH(h)$[ord(h)=pHourInitblock1h] = no;
nonInitH(h)$[ord(h)=pHourInitblockpeaknet2h] = no;
nonInitH(h)$[ord(h)=pHourInitblockpeaktotal3h] = no;
nonInitH(h)$[ord(h)=pHourInitblock4h] = no;
nonInitH(h)$[ord(h)=pHourInitblockpeaknetramp5h] = no;
nonInitH(h)$[ord(h)=pHourInitblock6h] = no;

Variables
	vInitSOCblock1h(storageegu)
	vInitSOCblockpeaknet2h(storageegu)
	vInitSOCblockpeaktotal3h(storageegu)
	vInitSOCblock4h(storageegu)
	vInitSOCblockpeaknetramp5h(storageegu)
	vInitSOCblock6h(storageegu)
	vInitSOCblock1htech(storagetech)
	vInitSOCblockpeaknet2htech(storagetech)
	vInitSOCblockpeaktotal3htech(storagetech)
	vInitSOCblock4htech(storagetech)
	vInitSOCblockpeaknetramp5htech(storagetech)
	vInitSOCblock6htech(storagetech)
	;

Equations
	varCost
	co2Ems
	defSOC(storageegu,h)
	genPlusUpResToSOC(storageegu,h)
	setInitSOCblock1hststorageegu(ststorageegu)
	setInitSOCblockpeaknet2hststorageegu(ststorageegu)
	setInitSOCblockpeaktotal3hststorageegu(ststorageegu)
	setInitSOCblock4hststorageegu(ststorageegu)
	setInitSOCblockpeaknetramp5hststorageegu(ststorageegu)
	setInitSOCblock6hststorageegu(ststorageegu)
	defSOCtech(storagetech,h)
	genPlusUpResToSOCtech(storagetech,h)
	setInitSOCblock1hststoragetech(ststoragetech)
	setInitSOCblockpeaknet2hststoragetech(ststoragetech)
	setInitSOCblockpeaktotal3hststoragetech(ststoragetech)
	setInitSOCblock4hststoragetech(ststoragetech)
	setInitSOCblockpeaknetramp5hststoragetech(ststoragetech)
	setInitSOCblock6hststoragetech(ststoragetech)
	rampUpblock0h(egu,block0h)
	rampUpblock1h(egu,block1h)
	rampUpblockpeaknet2h(egu,blockpeaknet2h)
	rampUpblockpeaktotal3h(egu,blockpeaktotal3h)
	rampUpblock4h(egu,block4h)
	rampUpblockpeaknetramp5h(egu,blockpeaknetramp5h)
	rampUpblock6h(egu,block6h)
	rampUpblock0htech(tech,block0h)
	rampUpblock1htech(tech,block1h)
	rampUpblockpeaknet2htech(tech,blockpeaknet2h)
	rampUpblockpeaktotal3htech(tech,blockpeaktotal3h)
	rampUpblock4htech(tech,block4h)
	rampUpblockpeaknetramp5htech(tech,blockpeaknetramp5h)
	rampUpblock6htech(tech,block6h)
	limitHydroGenblock0h(z)
	limitHydroGenblock1h(z)
	limitHydroGenblockpeaknet2h(z)
	limitHydroGenblockpeaktotal3h(z)
	limitHydroGenblock4h(z)
	limitHydroGenblockpeaknetramp5h(z)
	limitHydroGenblock6h(z)
	;

defSOC(storageegu,h).. vStateofcharge(storageegu,h) =e= pInitSOC(storageegu)$[ord(h)=pHourInitblock0h] + vInitSOCblock1h(storageegu)$[ord(h)=pHourInitblock1h] + vInitSOCblockpeaknet2h(storageegu)$[ord(h)=pHourInitblockpeaknet2h] + vInitSOCblockpeaktotal3h(storageegu)$[ord(h)=pHourInitblockpeaktotal3h] + vInitSOCblock4h(storageegu)$[ord(h)=pHourInitblock4h] + vInitSOCblockpeaknetramp5h(storageegu)$[ord(h)=pHourInitblockpeaknetramp5h] + vInitSOCblock6h(storageegu)$[ord(h)=pHourInitblock6h] +
	vStateofcharge(storageegu, h-1)$nonInitH(h) - 
               1/sqrt(pEfficiency(storageegu)) * vGen(storageegu,h) + 
               sqrt(pEfficiency(storageegu)) * vCharge(storageegu,h);
genPlusUpResToSOC(storageegu,h).. vGen(storageegu,h)+vRegup(storageegu,h)+vFlex(storageegu,h)+vCont(storageegu,h) =l= vStateofcharge(storageegu, h-1)$nonInitH(h)
                     + pInitSOC(storageegu)$[ord(h)=pHourInitblock0h] + vInitSOCblock1h(storageegu)$[ord(h)=pHourInitblock1h] + vInitSOCblockpeaknet2h(storageegu)$[ord(h)=pHourInitblockpeaknet2h] + vInitSOCblockpeaktotal3h(storageegu)$[ord(h)=pHourInitblockpeaktotal3h] + vInitSOCblock4h(storageegu)$[ord(h)=pHourInitblock4h] + vInitSOCblockpeaknetramp5h(storageegu)$[ord(h)=pHourInitblockpeaknetramp5h] + vInitSOCblock6h(storageegu)$[ord(h)=pHourInitblock6h];
setInitSOCblock1hststorageegu(ststorageegu).. vInitSOCblock1h(ststorageegu) =e= 
                                    pInitSOC(ststorageegu);
setInitSOCblockpeaknet2hststorageegu(ststorageegu).. vInitSOCblockpeaknet2h(ststorageegu) =e= 
                                    pInitSOC(ststorageegu);
setInitSOCblockpeaktotal3hststorageegu(ststorageegu).. vInitSOCblockpeaktotal3h(ststorageegu) =e= 
                                    pInitSOC(ststorageegu);
setInitSOCblock4hststorageegu(ststorageegu).. vInitSOCblock4h(ststorageegu) =e= 
                                    pInitSOC(ststorageegu);
setInitSOCblockpeaknetramp5hststorageegu(ststorageegu).. vInitSOCblockpeaknetramp5h(ststorageegu) =e= 
                                    pInitSOC(ststorageegu);
setInitSOCblock6hststorageegu(ststorageegu).. vInitSOCblock6h(ststorageegu) =e= 
                                    pInitSOC(ststorageegu);

defSOCtech(storagetech,h).. vStateofchargetech(storagetech,h) =e= pInitSOCtech(storagetech)$[ord(h)=pHourInitblock0h]*vEneBuiltSto(storagetech) + vInitSOCblock1htech(storagetech)$[ord(h)=pHourInitblock1h] + vInitSOCblockpeaknet2htech(storagetech)$[ord(h)=pHourInitblockpeaknet2h] + vInitSOCblockpeaktotal3htech(storagetech)$[ord(h)=pHourInitblockpeaktotal3h] + vInitSOCblock4htech(storagetech)$[ord(h)=pHourInitblock4h] + vInitSOCblockpeaknetramp5htech(storagetech)$[ord(h)=pHourInitblockpeaknetramp5h] + vInitSOCblock6htech(storagetech)$[ord(h)=pHourInitblock6h] +
	vStateofchargetech(storagetech, h-1)$nonInitH(h) - 
               1/sqrt(pEfficiencytech(storagetech)) * vGentech(storagetech,h) + 
               sqrt(pEfficiencytech(storagetech)) * vChargetech(storagetech,h);
genPlusUpResToSOCtech(storagetech,h).. vGentech(storagetech,h)+vReguptech(storagetech,h)+vFlextech(storagetech,h)+vConttech(storagetech,h) =l= vStateofchargetech(storagetech, h-1)$nonInitH(h)
                     + pInitSOCtech(storagetech)$[ord(h)=pHourInitblock0h]*vEneBuiltSto(storagetech) + vInitSOCblock1htech(storagetech)$[ord(h)=pHourInitblock1h] + vInitSOCblockpeaknet2htech(storagetech)$[ord(h)=pHourInitblockpeaknet2h] + vInitSOCblockpeaktotal3htech(storagetech)$[ord(h)=pHourInitblockpeaktotal3h] + vInitSOCblock4htech(storagetech)$[ord(h)=pHourInitblock4h] + vInitSOCblockpeaknetramp5htech(storagetech)$[ord(h)=pHourInitblockpeaknetramp5h] + vInitSOCblock6htech(storagetech)$[ord(h)=pHourInitblock6h];
setInitSOCblock1hststoragetech(ststoragetech).. vInitSOCblock1htech(ststoragetech) =e= 
                                    pInitSOCtech(ststoragetech)*vEneBuiltSto(ststoragetech);
setInitSOCblockpeaknet2hststoragetech(ststoragetech).. vInitSOCblockpeaknet2htech(ststoragetech) =e= 
                                    pInitSOCtech(ststoragetech)*vEneBuiltSto(ststoragetech);
setInitSOCblockpeaktotal3hststoragetech(ststoragetech).. vInitSOCblockpeaktotal3htech(ststoragetech) =e= 
                                    pInitSOCtech(ststoragetech)*vEneBuiltSto(ststoragetech);
setInitSOCblock4hststoragetech(ststoragetech).. vInitSOCblock4htech(ststoragetech) =e= 
                                    pInitSOCtech(ststoragetech)*vEneBuiltSto(ststoragetech);
setInitSOCblockpeaknetramp5hststoragetech(ststoragetech).. vInitSOCblockpeaknetramp5htech(ststoragetech) =e= 
                                    pInitSOCtech(ststoragetech)*vEneBuiltSto(ststoragetech);
setInitSOCblock6hststoragetech(ststoragetech).. vInitSOCblock6htech(ststoragetech) =e= 
                                    pInitSOCtech(ststoragetech)*vEneBuiltSto(ststoragetech);

varCost.. vVarcostannual =e= pWeightblock0h*(sum((egu,block0h),vVarcost(egu,block0h))+sum((tech,block0h),vVarcosttech(tech,block0h)))
	+ pWeightblock1h*(sum((egu,block1h),vVarcost(egu,block1h))+sum((tech,block1h),vVarcosttech(tech,block1h)))
	+ pWeightblockpeaknet2h*(sum((egu,blockpeaknet2h),vVarcost(egu,blockpeaknet2h))+sum((tech,blockpeaknet2h),vVarcosttech(tech,blockpeaknet2h)))
	+ pWeightblockpeaktotal3h*(sum((egu,blockpeaktotal3h),vVarcost(egu,blockpeaktotal3h))+sum((tech,blockpeaktotal3h),vVarcosttech(tech,blockpeaktotal3h)))
	+ pWeightblock4h*(sum((egu,block4h),vVarcost(egu,block4h))+sum((tech,block4h),vVarcosttech(tech,block4h)))
	+ pWeightblockpeaknetramp5h*(sum((egu,blockpeaknetramp5h),vVarcost(egu,blockpeaknetramp5h))+sum((tech,blockpeaknetramp5h),vVarcosttech(tech,blockpeaknetramp5h)))
	+ pWeightblock6h*(sum((egu,block6h),vVarcost(egu,block6h))+sum((tech,block6h),vVarcosttech(tech,block6h)));
co2Ems.. vCO2emsannual =e= pWeightblock0h*(sum((egu,block0h),vCO2ems(egu,block0h))+sum((tech,block0h),vCO2emstech(tech,block0h)))
	+ pWeightblock1h*(sum((egu,block1h),vCO2ems(egu,block1h))+sum((tech,block1h),vCO2emstech(tech,block1h)))
	+ pWeightblockpeaknet2h*(sum((egu,blockpeaknet2h),vCO2ems(egu,blockpeaknet2h))+sum((tech,blockpeaknet2h),vCO2emstech(tech,blockpeaknet2h)))
	+ pWeightblockpeaktotal3h*(sum((egu,blockpeaktotal3h),vCO2ems(egu,blockpeaktotal3h))+sum((tech,blockpeaktotal3h),vCO2emstech(tech,blockpeaktotal3h)))
	+ pWeightblock4h*(sum((egu,block4h),vCO2ems(egu,block4h))+sum((tech,block4h),vCO2emstech(tech,block4h)))
	+ pWeightblockpeaknetramp5h*(sum((egu,blockpeaknetramp5h),vCO2ems(egu,blockpeaknetramp5h))+sum((tech,blockpeaknetramp5h),vCO2emstech(tech,blockpeaknetramp5h)))
	+ pWeightblock6h*(sum((egu,block6h),vCO2ems(egu,block6h))+sum((tech,block6h),vCO2emstech(tech,block6h)));

limitHydroGenblock0h(z)..sum((hydroegu,block0h)$[pGenzone(hydroegu)=ORD(z)],vGen(hydroegu,block0h)) =l= pMaxgenhydroblock0h(z);
limitHydroGenblock1h(z)..sum((hydroegu,block1h)$[pGenzone(hydroegu)=ORD(z)],vGen(hydroegu,block1h)) =l= pMaxgenhydroblock1h(z);
limitHydroGenblockpeaknet2h(z)..sum((hydroegu,blockpeaknet2h)$[pGenzone(hydroegu)=ORD(z)],vGen(hydroegu,blockpeaknet2h)) =l= pMaxgenhydroblockpeaknet2h(z);
limitHydroGenblockpeaktotal3h(z)..sum((hydroegu,blockpeaktotal3h)$[pGenzone(hydroegu)=ORD(z)],vGen(hydroegu,blockpeaktotal3h)) =l= pMaxgenhydroblockpeaktotal3h(z);
limitHydroGenblock4h(z)..sum((hydroegu,block4h)$[pGenzone(hydroegu)=ORD(z)],vGen(hydroegu,block4h)) =l= pMaxgenhydroblock4h(z);
limitHydroGenblockpeaknetramp5h(z)..sum((hydroegu,blockpeaknetramp5h)$[pGenzone(hydroegu)=ORD(z)],vGen(hydroegu,blockpeaknetramp5h)) =l= pMaxgenhydroblockpeaknetramp5h(z);
limitHydroGenblock6h(z)..sum((hydroegu,block6h)$[pGenzone(hydroegu)=ORD(z)],vGen(hydroegu,block6h)) =l= pMaxgenhydroblock6h(z);

rampUpblock0h(egu,block0h)$[ORD(block0h)>1].. vGen(egu,block0h)+vRegup(egu,block0h)+vFlex(egu,block0h)+vCont(egu,block0h) - vGen(egu,block0h-1) =l= 
                  pRamprate(egu);
rampUpblock0htech(tech,block0h)$[ORD(block0h)>1].. vGentech(tech,block0h)+vReguptech(tech,block0h)+vFlextech(tech,block0h)+vConttech(tech,block0h) - vGentech(tech,block0h-1) =l= 
                  pRampratetech(tech)*vN(tech);
rampUpblock1h(egu,block1h)$[ORD(block1h)>1].. vGen(egu,block1h)+vRegup(egu,block1h)+vFlex(egu,block1h)+vCont(egu,block1h) - vGen(egu,block1h-1) =l= 
                  pRamprate(egu);
rampUpblock1htech(tech,block1h)$[ORD(block1h)>1].. vGentech(tech,block1h)+vReguptech(tech,block1h)+vFlextech(tech,block1h)+vConttech(tech,block1h) - vGentech(tech,block1h-1) =l= 
                  pRampratetech(tech)*vN(tech);
rampUpblockpeaknet2h(egu,blockpeaknet2h)$[ORD(blockpeaknet2h)>1].. vGen(egu,blockpeaknet2h)+vRegup(egu,blockpeaknet2h)+vFlex(egu,blockpeaknet2h)+vCont(egu,blockpeaknet2h) - vGen(egu,blockpeaknet2h-1) =l= 
                  pRamprate(egu);
rampUpblockpeaknet2htech(tech,blockpeaknet2h)$[ORD(blockpeaknet2h)>1].. vGentech(tech,blockpeaknet2h)+vReguptech(tech,blockpeaknet2h)+vFlextech(tech,blockpeaknet2h)+vConttech(tech,blockpeaknet2h) - vGentech(tech,blockpeaknet2h-1) =l= 
                  pRampratetech(tech)*vN(tech);
rampUpblockpeaktotal3h(egu,blockpeaktotal3h)$[ORD(blockpeaktotal3h)>1].. vGen(egu,blockpeaktotal3h)+vRegup(egu,blockpeaktotal3h)+vFlex(egu,blockpeaktotal3h)+vCont(egu,blockpeaktotal3h) - vGen(egu,blockpeaktotal3h-1) =l= 
                  pRamprate(egu);
rampUpblockpeaktotal3htech(tech,blockpeaktotal3h)$[ORD(blockpeaktotal3h)>1].. vGentech(tech,blockpeaktotal3h)+vReguptech(tech,blockpeaktotal3h)+vFlextech(tech,blockpeaktotal3h)+vConttech(tech,blockpeaktotal3h) - vGentech(tech,blockpeaktotal3h-1) =l= 
                  pRampratetech(tech)*vN(tech);
rampUpblock4h(egu,block4h)$[ORD(block4h)>1].. vGen(egu,block4h)+vRegup(egu,block4h)+vFlex(egu,block4h)+vCont(egu,block4h) - vGen(egu,block4h-1) =l= 
                  pRamprate(egu);
rampUpblock4htech(tech,block4h)$[ORD(block4h)>1].. vGentech(tech,block4h)+vReguptech(tech,block4h)+vFlextech(tech,block4h)+vConttech(tech,block4h) - vGentech(tech,block4h-1) =l= 
                  pRampratetech(tech)*vN(tech);
rampUpblockpeaknetramp5h(egu,blockpeaknetramp5h)$[ORD(blockpeaknetramp5h)>1].. vGen(egu,blockpeaknetramp5h)+vRegup(egu,blockpeaknetramp5h)+vFlex(egu,blockpeaknetramp5h)+vCont(egu,blockpeaknetramp5h) - vGen(egu,blockpeaknetramp5h-1) =l= 
                  pRamprate(egu);
rampUpblockpeaknetramp5htech(tech,blockpeaknetramp5h)$[ORD(blockpeaknetramp5h)>1].. vGentech(tech,blockpeaknetramp5h)+vReguptech(tech,blockpeaknetramp5h)+vFlextech(tech,blockpeaknetramp5h)+vConttech(tech,blockpeaknetramp5h) - vGentech(tech,blockpeaknetramp5h-1) =l= 
                  pRampratetech(tech)*vN(tech);
rampUpblock6h(egu,block6h)$[ORD(block6h)>1].. vGen(egu,block6h)+vRegup(egu,block6h)+vFlex(egu,block6h)+vCont(egu,block6h) - vGen(egu,block6h-1) =l= 
                  pRamprate(egu);
rampUpblock6htech(tech,block6h)$[ORD(block6h)>1].. vGentech(tech,block6h)+vReguptech(tech,block6h)+vFlextech(tech,block6h)+vConttech(tech,block6h) - vGentech(tech,block6h-1) =l= 
                  pRampratetech(tech)*vN(tech);
