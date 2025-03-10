#!/bin/bash

for interconn in EI; do
  for co2Cap in 32448000; do
    for solarGenFracOfDemand in 0; do
      for windGenFracOfDemand in 0; do
        for scenario_key in CurrentZoning; do
          for economic_impacts in EIMs; do
            for eim_measure in ValueAdded; do  
              for tx_distance in SolarTxAll; do
	              for capex_discount_rate in 0.1; do
                  for costWgt in 0.8; do
                    sbatch RunMacroCEMJob.sbat "$interconn" "$co2Cap" "$solarGenFracOfDemand" "$windGenFracOfDemand" "$scenario_key" "$economic_impacts" "$eim_measure" "$tx_distance" "$capex_discount_rate" "$costWgt"
                    sleep 20s
                  done
                done
              done
            done
          done
        done
      done
    done
  done
done