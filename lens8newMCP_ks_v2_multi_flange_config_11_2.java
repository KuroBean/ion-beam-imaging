/*
 * lens8newMCP_ks_v2_multi_flange_config_11_2.java
 */

import com.comsol.model.*;
import com.comsol.model.util.*;

/** Model exported on Nov 4 2026, 13:58 by COMSOL 5.5.0.359. */
public class lens8newMCP_ks_v2_multi_flange_config_11_2 {

  public static Model run() {
    Model model = ModelUtil.create("Model");

    model.modelPath("D:\\Users\\kshimojo\\projects\\ion_beam_measurement");

    model.component().create("comp1", true);

    model.component("comp1").geom().create("geom1", 3);

    model.component("comp1").mesh().create("mesh1");

    model.component("comp1").physics().create("cpt", "ChargedParticleTracing", "geom1");
    model.component("comp1").physics().create("es", "Electrostatics", "geom1");

    model.component("comp1").geom("geom1").run();

    model.component("comp1").physics().move("es", 0);

    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").run("");
    model.component("comp1").geom("geom1").create("cyl1", "Cylinder");
    model.component("comp1").geom("geom1").lengthUnit("mm");
    model.component("comp1").geom("geom1").feature("cyl1").set("h", 300);
    model.component("comp1").geom("geom1").feature("cyl1").set("r", 75);
    model.component("comp1").geom("geom1").runPre("fin");

    model.component("comp1").view("view1").camera().set("projection", "perspective");
    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl1");
    model.component("comp1").view("view1").set("hidestatus", "showonlyhidden");
    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideObjects().clear();

    model.component("comp1").geom("geom1").run("cyl1");
    model.component("comp1").geom("geom1").runPre("fin");

    model.component("comp1").view("view1").set("hidestatus", "ignore");

    model.component("comp1").geom("geom1").run("cyl1");
    model.component("comp1").geom("geom1").create("wp1", "WorkPlane");
    model.component("comp1").geom("geom1").feature("wp1").set("unite", true);
    model.component("comp1").geom("geom1").feature("wp1").set("quickplane", "yz");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("wp1").geom().create("r1", "Rectangle");
    model.component("comp1").geom("geom1").feature("wp1").geom().feature("r1").set("size", new int[]{300, 75});
    model.component("comp1").geom("geom1").feature("wp1").geom().run("r1");
    model.component("comp1").geom("geom1").feature("wp1").geom().run("r1");
    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").feature("wp1").geom().feature("r1").set("rot", 90);
    model.component("comp1").geom("geom1").feature("wp1").geom().run("r1");
    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").feature("wp1").geom().feature("r1").active(false);
    model.component("comp1").geom("geom1").feature("wp1").geom().run("r1");
    model.component("comp1").geom("geom1").feature("wp1").geom().create("cro1", "CrossSection");
    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").run("wp1");
    model.component("comp1").geom("geom1").create("cyl2", "Cylinder");
    model.component("comp1").geom("geom1").feature("cyl2").set("h", 10);
    model.component("comp1").geom("geom1").run("cyl2");
    model.component("comp1").geom("geom1").run();

    model.component("comp1").physics("es").create("gnd1", "Ground", 2);
    model.component("comp1").physics("es").feature("gnd1").selection().set(3);
    model.component("comp1").physics("es").feature("gnd1").selection().all();
    model.component("comp1").physics("es").create("pot1", "ElectricPotential", 2);
    model.component("comp1").physics("es").feature("pot1").set("V0", -100);
    model.component("comp1").physics("es").feature("pot1").selection().set(4, 12);

    model.study().create("std1");
    model.study("std1").create("stat", "Stationary");
    model.study("std1").feature("stat").activate("es", true);
    model.study("std1").feature("stat").activate("cpt", true);
    model.study("std1").feature("stat").setIndex("activate", false, 3);

    model.sol().create("sol1");
    model.sol("sol1").study("std1");
    model.sol("sol1").attach("std1");

    model.component("comp1").physics("cpt").active(false);

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol1").attach("std1");

    model.result().create("pg1", "PlotGroup3D");
    model.result("pg1").label("Electric Potential (es)");
    model.result("pg1").set("frametype", "spatial");
    model.result("pg1").set("data", "dset1");
    model.result("pg1").feature().create("mslc1", "Multislice");
    model.result("pg1").feature("mslc1").set("colortable", "RainbowLight");
    model.result("pg1").feature("mslc1").set("data", "parent");
    model.result().remove("pg1");

    model.component("comp1").material().create("mat1", "Common");
    model.component("comp1").material("mat1").label("304L [solid,polished]");
    model.component("comp1").material("mat1").info().create("DIN");
    model.component("comp1").material("mat1").info("DIN").body("X2CrNi18-9/X2CrNi19-11");
    model.component("comp1").material("mat1").info().create("UNS");
    model.component("comp1").material("mat1").info("UNS").body("S30403");
    model.component("comp1").material("mat1").info().create("Composition");
    model.component("comp1").material("mat1").info("Composition")
         .body("bal. Fe, (18-22) Cr, (8-10.5) Ni, 0.03 C max, 2 Mn max, 0.1 N max, 0.045 P max, 0.03 S max, 1 Si max (wt%)");
    model.component("comp1").material("mat1").propertyGroup("def").set("thermalconductivity", "k(T[1/K])[W/(m*K)]");
    model.component("comp1").material("mat1").propertyGroup("def").set("resistivity", "res(T[1/K])[ohm*m]");
    model.component("comp1").material("mat1").propertyGroup("def")
         .set("thermalexpansioncoefficient", "(alpha(T[1/K])[1/K]+(Tempref-293[K])*if(abs(T-Tempref)>1e-3,(alpha(T[1/K])[1/K]-alpha(Tempref[1/K])[1/K])/(T-Tempref),d(alpha(T[1/K])[1/K],T)))/(1+alpha(Tempref[1/K])[1/K]*(Tempref-293[K]))");
    model.component("comp1").material("mat1").propertyGroup("def").set("heatcapacity", "C(T[1/K])[J/(kg*K)]");
    model.component("comp1").material("mat1").propertyGroup("def").set("electricconductivity", "sigma(T[1/K])[S/m]");
    model.component("comp1").material("mat1").propertyGroup("def")
         .set("emissivity", "epsilon_solid_polished_1(T[1/K])");
    model.component("comp1").material("mat1").propertyGroup("def").set("density", "rho(T[1/K])[kg/m^3]");
    model.component("comp1").material("mat1").propertyGroup("def").set("TD", "TD(T[1/K])[m^2/s]");
    model.component("comp1").material("mat1").propertyGroup("def").func().create("k", "Piecewise");
    model.component("comp1").material("mat1").propertyGroup("def").func("k").set("funcname", "k");
    model.component("comp1").material("mat1").propertyGroup("def").func("k").set("arg", "T");
    model.component("comp1").material("mat1").propertyGroup("def").func("k").set("extrap", "constant");
    model.component("comp1").material("mat1").propertyGroup("def").func("k")
         .set("pieces", new String[][]{{"1.0", "45.0", "-0.03740871+0.06460546*T^1+0.003720604*T^2-8.390067E-5*T^3+6.006594E-7*T^4"}, {"45.0", "283.0", "-1.031521+0.1813807*T^1-0.001088656*T^2+3.411681E-6*T^3-3.988389E-9*T^4"}, {"283.0", "887.0", "-1.258169+0.1023945*T^1-2.189547E-4*T^2+2.312931E-7*T^3-8.903937E-11*T^4"}});
    model.component("comp1").material("mat1").propertyGroup("def").func("k").label("Piecewise");
    model.component("comp1").material("mat1").propertyGroup("def").func("k").set("fununit", "");
    model.component("comp1").material("mat1").propertyGroup("def").func("k").set("argunit", "");
    model.component("comp1").material("mat1").propertyGroup("def").func().create("res", "Piecewise");
    model.component("comp1").material("mat1").propertyGroup("def").func("res").set("funcname", "res");
    model.component("comp1").material("mat1").propertyGroup("def").func("res").set("arg", "T");
    model.component("comp1").material("mat1").propertyGroup("def").func("res").set("extrap", "constant");
    model.component("comp1").material("mat1").propertyGroup("def").func("res")
         .set("pieces", new String[][]{{"1.0", "10.0", "4.85E-7"}, {"10.0", "273.0", "4.915758E-7-8.103548E-10*T^1+1.582349E-11*T^2-5.524795E-14*T^3+6.640058E-17*T^4"}, {"273.0", "1672.0", "4.15904E-7+1.170541E-9*T^1-5.839381E-13*T^2+1.201886E-16*T^3"}});
    model.component("comp1").material("mat1").propertyGroup("def").func("res").label("Piecewise 1");
    model.component("comp1").material("mat1").propertyGroup("def").func("res").set("fununit", "");
    model.component("comp1").material("mat1").propertyGroup("def").func("res").set("argunit", "");
    model.component("comp1").material("mat1").propertyGroup("def").func().create("alpha", "Piecewise");
    model.component("comp1").material("mat1").propertyGroup("def").func("alpha").set("funcname", "alpha");
    model.component("comp1").material("mat1").propertyGroup("def").func("alpha").set("arg", "T");
    model.component("comp1").material("mat1").propertyGroup("def").func("alpha").set("extrap", "constant");
    model.component("comp1").material("mat1").propertyGroup("def").func("alpha")
         .set("pieces", new String[][]{{"4.0", "249.0", "1.017247E-5+4.390756E-8*T^1-9.800292E-11*T^2-9.637483E-14*T^3+4.333114E-16*T^4"}, {"249.0", "1700.0", "1.356267E-5+6.945622E-9*T^1-1.444708E-12*T^2"}});
    model.component("comp1").material("mat1").propertyGroup("def").func("alpha").label("Piecewise 2");
    model.component("comp1").material("mat1").propertyGroup("def").func("alpha").set("fununit", "");
    model.component("comp1").material("mat1").propertyGroup("def").func("alpha").set("argunit", "");
    model.component("comp1").material("mat1").propertyGroup("def").func().create("C", "Piecewise");
    model.component("comp1").material("mat1").propertyGroup("def").func("C").set("funcname", "C");
    model.component("comp1").material("mat1").propertyGroup("def").func("C").set("arg", "T");
    model.component("comp1").material("mat1").propertyGroup("def").func("C").set("extrap", "constant");
    model.component("comp1").material("mat1").propertyGroup("def").func("C")
         .set("pieces", new String[][]{{"4.0", "14.0", "4.80349978-1.97398861*T^1+0.433444409*T^2-0.0314324757*T^3+8.32403453E-4*T^4"}, 
         {"14.0", "47.0", "-0.224295746+0.760568357*T^1-0.0400750758*T^2+0.00218176061*T^3-1.83602372E-5*T^4"}, 
         {"47.0", "128.0", "8.9262753-2.90098686*T^1+0.147079315*T^2-0.00125489708*T^3+3.41401137E-6*T^4"}, 
         {"128.0", "310.0", "270.215021-1.21051111*T^1+0.0215156635*T^2-7.51184063E-5*T^3+8.13679634E-8*T^4"}, 
         {"310.0", "1311.0", "109.207295+2.5717751*T^1-0.00652809855*T^2+7.78752439E-6*T^3-4.16791252E-9*T^4+8.09061335E-13*T^5"}});
    model.component("comp1").material("mat1").propertyGroup("def").func("C").label("Piecewise 3");
    model.component("comp1").material("mat1").propertyGroup("def").func("C").set("fununit", "");
    model.component("comp1").material("mat1").propertyGroup("def").func("C").set("argunit", "");
    model.component("comp1").material("mat1").propertyGroup("def").func().create("sigma", "Piecewise");
    model.component("comp1").material("mat1").propertyGroup("def").func("sigma").set("funcname", "sigma");
    model.component("comp1").material("mat1").propertyGroup("def").func("sigma").set("arg", "T");
    model.component("comp1").material("mat1").propertyGroup("def").func("sigma").set("extrap", "constant");
    model.component("comp1").material("mat1").propertyGroup("def").func("sigma")
         .set("pieces", new String[][]{{"1.0", "10.0", "1/(4.850000E-07)"}, {"10.0", "273.0", "1/(6.640058E-17*T^4-5.524795E-14*T^3+1.582349E-11*T^2-8.103548E-10*T+4.915758E-07)"}, {"273.0", "1672.0", "1/(1.201886E-16*T^3-5.839381E-13*T^2+1.170541E-09*T+4.159040E-07)"}});
    model.component("comp1").material("mat1").propertyGroup("def").func("sigma").label("Piecewise 4");
    model.component("comp1").material("mat1").propertyGroup("def").func("sigma").set("fununit", "");
    model.component("comp1").material("mat1").propertyGroup("def").func("sigma").set("argunit", "");
    model.component("comp1").material("mat1").propertyGroup("def").func()
         .create("epsilon_solid_polished_1", "Piecewise");
    model.component("comp1").material("mat1").propertyGroup("def").func("epsilon_solid_polished_1")
         .set("funcname", "epsilon_solid_polished_1");
    model.component("comp1").material("mat1").propertyGroup("def").func("epsilon_solid_polished_1").set("arg", "T");
    model.component("comp1").material("mat1").propertyGroup("def").func("epsilon_solid_polished_1")
         .set("extrap", "constant");
    model.component("comp1").material("mat1").propertyGroup("def").func("epsilon_solid_polished_1")
         .set("pieces", new String[][]{{"340.0", "1100.0", "0.03942897+2.131191E-4*T^1-6.420526E-8*T^2"}});
    model.component("comp1").material("mat1").propertyGroup("def").func("epsilon_solid_polished_1")
         .label("Piecewise 5");
    model.component("comp1").material("mat1").propertyGroup("def").func("epsilon_solid_polished_1")
         .set("fununit", "");
    model.component("comp1").material("mat1").propertyGroup("def").func("epsilon_solid_polished_1")
         .set("argunit", "");
    model.component("comp1").material("mat1").propertyGroup("def").func().create("rho", "Piecewise");
    model.component("comp1").material("mat1").propertyGroup("def").func("rho").set("funcname", "rho");
    model.component("comp1").material("mat1").propertyGroup("def").func("rho").set("arg", "T");
    model.component("comp1").material("mat1").propertyGroup("def").func("rho").set("extrap", "constant");
    model.component("comp1").material("mat1").propertyGroup("def").func("rho")
         .set("pieces", new String[][]{{"4.0", "93.0", "7930.967+0.03300298*T^1-9.663581E-4*T^2-2.917178E-6*T^3"}, {"93.0", "1700.0", "7945.333-0.1981948*T^1-3.713764E-4*T^2+2.213069E-7*T^3-5.128456E-11*T^4"}});
    model.component("comp1").material("mat1").propertyGroup("def").func("rho").label("Piecewise 6");
    model.component("comp1").material("mat1").propertyGroup("def").func("rho").set("fununit", "");
    model.component("comp1").material("mat1").propertyGroup("def").func("rho").set("argunit", "");
    model.component("comp1").material("mat1").propertyGroup("def").func().create("TD", "Piecewise");
    model.component("comp1").material("mat1").propertyGroup("def").func("TD").set("funcname", "TD");
    model.component("comp1").material("mat1").propertyGroup("def").func("TD").set("arg", "T");
    model.component("comp1").material("mat1").propertyGroup("def").func("TD").set("extrap", "constant");
    model.component("comp1").material("mat1").propertyGroup("def").func("TD")
         .set("pieces", new String[][]{{"291.0", "1273.0", "2.89744E-6+1.975182E-9*T^1-3.504974E-13*T^2"}});
    model.component("comp1").material("mat1").propertyGroup("def").func("TD").label("Piecewise 7");
    model.component("comp1").material("mat1").propertyGroup("def").func("TD").set("fununit", "");
    model.component("comp1").material("mat1").propertyGroup("def").func("TD").set("argunit", "");
    model.component("comp1").material("mat1").propertyGroup("def").addInput("temperature");
    model.component("comp1").material("mat1").propertyGroup("def").addInput("strainreferencetemperature");
    model.component("comp1").material("mat1").propertyGroup().create("ThermalExpansion", "Thermal expansion");
    model.component("comp1").material("mat1").propertyGroup("ThermalExpansion")
         .set("dL", "(dL(T[1/K])-dL(Tempref[1/K]))/(1+dL(Tempref[1/K]))");
    model.component("comp1").material("mat1").propertyGroup("ThermalExpansion")
         .set("dLIso", "(dL(T[1/K])-dL(Tempref[1/K]))/(1+dL(Tempref[1/K]))");
    model.component("comp1").material("mat1").propertyGroup("ThermalExpansion").set("alphatan", "CTE(T[1/K])[1/K]");
    model.component("comp1").material("mat1").propertyGroup("ThermalExpansion")
         .set("alphatanIso", "CTE(T[1/K])[1/K]");
    model.component("comp1").material("mat1").propertyGroup("ThermalExpansion").func().create("dL", "Piecewise");
    model.component("comp1").material("mat1").propertyGroup("ThermalExpansion").func("dL").set("funcname", "dL");
    model.component("comp1").material("mat1").propertyGroup("ThermalExpansion").func("dL").set("arg", "T");
    model.component("comp1").material("mat1").propertyGroup("ThermalExpansion").func("dL").set("extrap", "constant");
    model.component("comp1").material("mat1").propertyGroup("ThermalExpansion").func("dL")
         .set("pieces", new String[][]{{"4.0", "23.0", "-0.003001132"}, {"23.0", "293.0", "-0.00295624861-3.976809E-6*T^1+9.26213E-8*T^2-2.022102E-10*T^3+1.700751E-13*T^4+1.339137E-18*T^5"}, {"293.0", "1700.0", "-0.004250716+1.288108E-5*T^1+5.828938E-9*T^2-9.481366E-13*T^3"}});
    model.component("comp1").material("mat1").propertyGroup("ThermalExpansion").func("dL").label("Piecewise");
    model.component("comp1").material("mat1").propertyGroup("ThermalExpansion").func("dL").set("fununit", "");
    model.component("comp1").material("mat1").propertyGroup("ThermalExpansion").func("dL").set("argunit", "");
    model.component("comp1").material("mat1").propertyGroup("ThermalExpansion").func().create("CTE", "Piecewise");
    model.component("comp1").material("mat1").propertyGroup("ThermalExpansion").func("CTE").set("funcname", "CTE");
    model.component("comp1").material("mat1").propertyGroup("ThermalExpansion").func("CTE").set("arg", "T");
    model.component("comp1").material("mat1").propertyGroup("ThermalExpansion").func("CTE")
         .set("extrap", "constant");
    model.component("comp1").material("mat1").propertyGroup("ThermalExpansion").func("CTE")
         .set("pieces", new String[][]{{"10.0", "60.0", "-4.05E-7+2.2625E-8*T^1-3.647917E-9*T^2+1.275E-10*T^3-8.958333E-13*T^4"}, {"60.0", "200.0", "-9.799E-6+3.003203E-7*T^1-1.387121E-9*T^2+2.424242E-12*T^3"}, {"200.0", "300.0", "4.624037E-6+6.552795E-8*T^1-8.889364E-11*T^2"}});
    model.component("comp1").material("mat1").propertyGroup("ThermalExpansion").func("CTE").label("Piecewise 1");
    model.component("comp1").material("mat1").propertyGroup("ThermalExpansion").func("CTE").set("fununit", "");
    model.component("comp1").material("mat1").propertyGroup("ThermalExpansion").func("CTE").set("argunit", "");
    model.component("comp1").material("mat1").propertyGroup("ThermalExpansion").addInput("temperature");
    model.component("comp1").material("mat1").propertyGroup("ThermalExpansion")
         .addInput("strainreferencetemperature");
    model.component("comp1").material("mat1").propertyGroup().create("Enu", "Young's modulus and Poisson's ratio");
    model.component("comp1").material("mat1").propertyGroup("Enu").set("youngsmodulus", "E(T[1/K])[Pa]");
    model.component("comp1").material("mat1").propertyGroup("Enu").set("poissonsratio", "nu(T[1/K])");
    model.component("comp1").material("mat1").propertyGroup("Enu").func().create("E", "Piecewise");
    model.component("comp1").material("mat1").propertyGroup("Enu").func("E").set("funcname", "E");
    model.component("comp1").material("mat1").propertyGroup("Enu").func("E").set("arg", "T");
    model.component("comp1").material("mat1").propertyGroup("Enu").func("E").set("extrap", "constant");
    model.component("comp1").material("mat1").propertyGroup("Enu").func("E")
         .set("pieces", new String[][]{{"5.0", "60.0", "2.078364E11+7.414909E7*T^1"}, {"60.0", "295.0", "2.077579E11+1.570552E8*T^1-1651323.0*T^2+5296.944*T^3-6.38774*T^4"}, {"295.0", "1173.0", "2.242833E11-8.92503E7*T^1"}});
    model.component("comp1").material("mat1").propertyGroup("Enu").func("E").label("Piecewise");
    model.component("comp1").material("mat1").propertyGroup("Enu").func("E").set("fununit", "");
    model.component("comp1").material("mat1").propertyGroup("Enu").func("E").set("argunit", "");
    model.component("comp1").material("mat1").propertyGroup("Enu").func().create("nu", "Piecewise");
    model.component("comp1").material("mat1").propertyGroup("Enu").func("nu").set("funcname", "nu");
    model.component("comp1").material("mat1").propertyGroup("Enu").func("nu").set("arg", "T");
    model.component("comp1").material("mat1").propertyGroup("Enu").func("nu").set("extrap", "constant");
    model.component("comp1").material("mat1").propertyGroup("Enu").func("nu")
         .set("pieces", new String[][]{{"5.0", "60.0", "0.2797496-4.402647E-5*T^1"}, {"60.0", "295.0", "0.2752731+2.459471E-5*T^1+1.356199E-7*T^2-1.850087E-10*T^3"}, {"295.0", "1173.0", "0.2652448+8.224213E-5*T^1"}});
    model.component("comp1").material("mat1").propertyGroup("Enu").func("nu").label("Piecewise 1");
    model.component("comp1").material("mat1").propertyGroup("Enu").func("nu").set("fununit", "");
    model.component("comp1").material("mat1").propertyGroup("Enu").func("nu").set("argunit", "");
    model.component("comp1").material("mat1").propertyGroup("Enu").addInput("temperature");
    model.component("comp1").material("mat1").propertyGroup().create("KG", "Bulk modulus and shear modulus");
    model.component("comp1").material("mat1").propertyGroup("KG").set("G", "mu(T[1/K])[Pa]");
    model.component("comp1").material("mat1").propertyGroup("KG").set("K", "kappa(T[1/K])[Pa]");
    model.component("comp1").material("mat1").propertyGroup("KG").func().create("mu", "Piecewise");
    model.component("comp1").material("mat1").propertyGroup("KG").func("mu").set("funcname", "mu");
    model.component("comp1").material("mat1").propertyGroup("KG").func("mu").set("arg", "T");
    model.component("comp1").material("mat1").propertyGroup("KG").func("mu").set("extrap", "constant");
    model.component("comp1").material("mat1").propertyGroup("KG").func("mu")
         .set("pieces", new String[][]{{"5.0", "60.0", "8.006021E10+3.177818E7*T^1"}, {"60.0", "295.0", "8.029302E10+6.039092E7*T^1-659731.6*T^2+2106.197*T^3-2.525896*T^4"}, {"295.0", "1173.0", "8.670748E10-3.756766E7*T^1"}});
    model.component("comp1").material("mat1").propertyGroup("KG").func("mu").label("Piecewise");
    model.component("comp1").material("mat1").propertyGroup("KG").func("mu").set("fununit", "");
    model.component("comp1").material("mat1").propertyGroup("KG").func("mu").set("argunit", "");
    model.component("comp1").material("mat1").propertyGroup("KG").func().create("kappa", "Piecewise");
    model.component("comp1").material("mat1").propertyGroup("KG").func("kappa").set("funcname", "kappa");
    model.component("comp1").material("mat1").propertyGroup("KG").func("kappa").set("arg", "T");
    model.component("comp1").material("mat1").propertyGroup("KG").func("kappa").set("extrap", "constant");
    model.component("comp1").material("mat1").propertyGroup("KG").func("kappa")
         .set("pieces", new String[][]{{"293.0", "870.0", "1.727914E11-5205743.0*T^1"}});
    model.component("comp1").material("mat1").propertyGroup("KG").func("kappa").label("Piecewise 1");
    model.component("comp1").material("mat1").propertyGroup("KG").func("kappa").set("fununit", "");
    model.component("comp1").material("mat1").propertyGroup("KG").func("kappa").set("argunit", "");
    model.component("comp1").material("mat1").propertyGroup("KG").addInput("temperature");
    model.component("comp1").material("mat1").set("family", "iron");

    model.component("comp1").view("view1").set("renderwireframe", false);

    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature().move("cyl2", 1);
    model.component("comp1").geom("geom1").run();
    model.component("comp1").geom("geom1").feature().duplicate("cyl3", "cyl1");
    model.component("comp1").geom("geom1").feature().move("cyl3", 1);
    model.component("comp1").geom("geom1").feature("cyl3").set("r", 80);
    model.component("comp1").geom("geom1").feature("cyl3").set("h", 310);
    model.component("comp1").geom("geom1").feature("cyl3").set("r", 85);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl3").set("pos", new int[]{0, 0, -5});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("wp1");
    model.component("comp1").geom("geom1").create("dif1", "Difference");
    model.component("comp1").geom("geom1").feature().remove("dif1");
    model.component("comp1").geom("geom1").run();

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);

    model.component("comp1").geom("geom1").run("wp1");
    model.component("comp1").geom("geom1").create("par1", "Partition");
    model.component("comp1").geom("geom1").feature("par1").selection("input").set("cyl3");

    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl3");
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl3");
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl3");
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl3");
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl3");
    model.component("comp1").view("view1").set("hidestatus", "hide");

    model.component("comp1").geom("geom1").feature("par1").selection("tool").set("cyl1");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.component("comp1").geom("geom1").feature("par1").active(false);
    model.component("comp1").geom("geom1").run("par1");
    model.component("comp1").geom("geom1").create("dif1", "Difference");
    model.component("comp1").geom("geom1").feature("dif1").selection("input").set("cyl3");

    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl3");

    model.component("comp1").geom("geom1").feature("dif1").selection("input2").set("cyl1");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature().move("dif1", 3);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.component("comp1").material("mat1").selection().set(1, 2, 3, 4);

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);

    model.component("comp1").material("mat1").propertyGroup("def").set("relpermittivity", new String[]{"1"});
    model.component("comp1").material().create("mat2", "Common");
    model.component("comp1").material("mat2").label("Corning 7740 (Pyrex) [solid,1.05 mm thick]");
    model.component("comp1").material("mat2").info().create("Composition");
    model.component("comp1").material("mat2").info("Composition")
         .body("80.5 SiO2, 12.9 B2O3, 3.8 Na2O, 2.2 Al2O3 (wt%)");
    model.component("comp1").material("mat2").propertyGroup("def").set("thermalconductivity", "k(T[1/K])[W/(m*K)]");
    model.component("comp1").material("mat2").propertyGroup("def").set("resistivity", "res(T[1/K])[ohm*m]");
    model.component("comp1").material("mat2").propertyGroup("def")
         .set("thermalexpansioncoefficient", "(alpha(T[1/K])[1/K]+(Tempref-293[K])*if(abs(T-Tempref)>1e-3,(alpha(T[1/K])[1/K]-alpha(Tempref[1/K])[1/K])/(T-Tempref),d(alpha(T[1/K])[1/K],T)))/(1+alpha(Tempref[1/K])[1/K]*(Tempref-293[K]))");
    model.component("comp1").material("mat2").propertyGroup("def").set("heatcapacity", "C(T[1/K])[J/(kg*K)]");
    model.component("comp1").material("mat2").propertyGroup("def").set("electricconductivity", "sigma(T[1/K])[S/m]");
    model.component("comp1").material("mat2").propertyGroup("def")
         .set("emissivity", "epsilon_solid_1_05_mm_thick_1(T[1/K])");
    model.component("comp1").material("mat2").propertyGroup("def").set("density", "rho(T[1/K])[kg/m^3]");
    model.component("comp1").material("mat2").propertyGroup("def").set("TD", "TD(T[1/K])[m^2/s]");
    model.component("comp1").material("mat2").propertyGroup("def").set("nemiss", "nemiss(T[1/K])");
    model.component("comp1").material("mat2").propertyGroup("def").func().create("k", "Piecewise");
    model.component("comp1").material("mat2").propertyGroup("def").func("k").set("funcname", "k");
    model.component("comp1").material("mat2").propertyGroup("def").func("k").set("arg", "T");
    model.component("comp1").material("mat2").propertyGroup("def").func("k").set("extrap", "constant");
    model.component("comp1").material("mat2").propertyGroup("def").func("k")
         .set("pieces", new String[][]{{"90.0", "522.0", "0.1448239+0.00500369*T^1-6.929144E-6*T^2+3.477568E-9*T^3"}});
    model.component("comp1").material("mat2").propertyGroup("def").func("k").label("Piecewise");
    model.component("comp1").material("mat2").propertyGroup("def").func("k").set("fununit", "");
    model.component("comp1").material("mat2").propertyGroup("def").func("k").set("argunit", "");
    model.component("comp1").material("mat2").propertyGroup("def").func().create("res", "Piecewise");
    model.component("comp1").material("mat2").propertyGroup("def").func("res").set("funcname", "res");
    model.component("comp1").material("mat2").propertyGroup("def").func("res").set("arg", "T");
    model.component("comp1").material("mat2").propertyGroup("def").func("res").set("extrap", "constant");
    model.component("comp1").material("mat2").propertyGroup("def").func("res")
         .set("pieces", new String[][]{{"293.0", "423.0", "exp(1.378133E-09*T^4 - 2.629179E-06*T^3 + 1.992116E-03*T^2 - 7.492484E-01*T + 1.440200E+02)"}});
    model.component("comp1").material("mat2").propertyGroup("def").func("res").label("Piecewise 1");
    model.component("comp1").material("mat2").propertyGroup("def").func("res").set("fununit", "");
    model.component("comp1").material("mat2").propertyGroup("def").func("res").set("argunit", "");
    model.component("comp1").material("mat2").propertyGroup("def").func().create("alpha", "Piecewise");

    return model;
  }

  public static Model run2(Model model) {
    model.component("comp1").material("mat2").propertyGroup("def").func("alpha").set("funcname", "alpha");
    model.component("comp1").material("mat2").propertyGroup("def").func("alpha").set("arg", "T");
    model.component("comp1").material("mat2").propertyGroup("def").func("alpha").set("extrap", "constant");
    model.component("comp1").material("mat2").propertyGroup("def").func("alpha")
         .set("pieces", new String[][]{{"0.0", "160.0", "1.851582E-6+1.163474E-8*T^1-4.953918E-11*T^2+8.923476E-14*T^3"}, {"160.0", "673.0", "2.186498E-6+5.435716E-9*T^1-1.068489E-11*T^2+7.4749E-15*T^3"}});
    model.component("comp1").material("mat2").propertyGroup("def").func("alpha").label("Piecewise 2");
    model.component("comp1").material("mat2").propertyGroup("def").func("alpha").set("fununit", "");
    model.component("comp1").material("mat2").propertyGroup("def").func("alpha").set("argunit", "");
    model.component("comp1").material("mat2").propertyGroup("def").func().create("C", "Piecewise");
    model.component("comp1").material("mat2").propertyGroup("def").func("C").set("funcname", "C");
    model.component("comp1").material("mat2").propertyGroup("def").func("C").set("arg", "T");
    model.component("comp1").material("mat2").propertyGroup("def").func("C").set("extrap", "constant");
    model.component("comp1").material("mat2").propertyGroup("def").func("C")
         .set("pieces", new String[][]{{"20.0", "700.0", "-54.4514965+3.65056845*T^1-0.00360243572*T^2+1.22855043E-6*T^3"}});
    model.component("comp1").material("mat2").propertyGroup("def").func("C").label("Piecewise 3");
    model.component("comp1").material("mat2").propertyGroup("def").func("C").set("fununit", "");
    model.component("comp1").material("mat2").propertyGroup("def").func("C").set("argunit", "");
    model.component("comp1").material("mat2").propertyGroup("def").func().create("sigma", "Piecewise");
    model.component("comp1").material("mat2").propertyGroup("def").func("sigma").set("funcname", "sigma");
    model.component("comp1").material("mat2").propertyGroup("def").func("sigma").set("arg", "T");
    model.component("comp1").material("mat2").propertyGroup("def").func("sigma").set("extrap", "constant");
    model.component("comp1").material("mat2").propertyGroup("def").func("sigma")
         .set("pieces", new String[][]{{"293.0", "423.0", "1/(exp(1.378133E-09*T^4-2.629179E-06*T^3+1.992116E-03*T^2-7.492484E-01*T+1.440200E+02))"}});
    model.component("comp1").material("mat2").propertyGroup("def").func("sigma").label("Piecewise 4");
    model.component("comp1").material("mat2").propertyGroup("def").func("sigma").set("fununit", "");
    model.component("comp1").material("mat2").propertyGroup("def").func("sigma").set("argunit", "");
    model.component("comp1").material("mat2").propertyGroup("def").func()
         .create("epsilon_solid_1_05_mm_thick_1", "Piecewise");
    model.component("comp1").material("mat2").propertyGroup("def").func("epsilon_solid_1_05_mm_thick_1")
         .set("funcname", "epsilon_solid_1_05_mm_thick_1");
    model.component("comp1").material("mat2").propertyGroup("def").func("epsilon_solid_1_05_mm_thick_1")
         .set("arg", "T");
    model.component("comp1").material("mat2").propertyGroup("def").func("epsilon_solid_1_05_mm_thick_1")
         .set("extrap", "constant");
    model.component("comp1").material("mat2").propertyGroup("def").func("epsilon_solid_1_05_mm_thick_1")
         .set("pieces", new String[][]{{"293.0", "480.0", "0.8478935-1.877544E-4*T^1"}, {"480.0", "720.0", "0.7689194+1.869195E-4*T^1-4.372668E-7*T^2"}});
    model.component("comp1").material("mat2").propertyGroup("def").func("epsilon_solid_1_05_mm_thick_1")
         .label("Piecewise 5");
    model.component("comp1").material("mat2").propertyGroup("def").func("epsilon_solid_1_05_mm_thick_1")
         .set("fununit", "");
    model.component("comp1").material("mat2").propertyGroup("def").func("epsilon_solid_1_05_mm_thick_1")
         .set("argunit", "");
    model.component("comp1").material("mat2").propertyGroup("def").func().create("rho", "Piecewise");
    model.component("comp1").material("mat2").propertyGroup("def").func("rho").set("funcname", "rho");
    model.component("comp1").material("mat2").propertyGroup("def").func("rho").set("arg", "T");
    model.component("comp1").material("mat2").propertyGroup("def").func("rho").set("extrap", "constant");
    model.component("comp1").material("mat2").propertyGroup("def").func("rho")
         .set("pieces", new String[][]{{"0.0", "80.0", "2233.66+0.002833638*T^1+6.584951E-5*T^2-1.396822E-6*T^3"}, {"80.0", "673.0", "2234.113-0.002096489*T^1-6.441875E-5*T^2+9.703111E-8*T^3-5.572413E-11*T^4"}});
    model.component("comp1").material("mat2").propertyGroup("def").func("rho").label("Piecewise 6");
    model.component("comp1").material("mat2").propertyGroup("def").func("rho").set("fununit", "");
    model.component("comp1").material("mat2").propertyGroup("def").func("rho").set("argunit", "");
    model.component("comp1").material("mat2").propertyGroup("def").func().create("TD", "Piecewise");
    model.component("comp1").material("mat2").propertyGroup("def").func("TD").set("funcname", "TD");
    model.component("comp1").material("mat2").propertyGroup("def").func("TD").set("arg", "T");
    model.component("comp1").material("mat2").propertyGroup("def").func("TD").set("extrap", "constant");
    model.component("comp1").material("mat2").propertyGroup("def").func("TD")
         .set("pieces", new String[][]{{"293.0", "633.0", "5.738761E-7-1.01864E-10*T^1"}});
    model.component("comp1").material("mat2").propertyGroup("def").func("TD").label("Piecewise 7");
    model.component("comp1").material("mat2").propertyGroup("def").func("TD").set("fununit", "");
    model.component("comp1").material("mat2").propertyGroup("def").func("TD").set("argunit", "");
    model.component("comp1").material("mat2").propertyGroup("def").func().create("nemiss", "Piecewise");
    model.component("comp1").material("mat2").propertyGroup("def").func("nemiss").set("funcname", "nemiss");
    model.component("comp1").material("mat2").propertyGroup("def").func("nemiss").set("arg", "T");
    model.component("comp1").material("mat2").propertyGroup("def").func("nemiss").set("extrap", "constant");
    model.component("comp1").material("mat2").propertyGroup("def").func("nemiss")
         .set("pieces", new String[][]{{"80.0", "1086.0", "0.878232-6.238731E-5*T^1"}});
    model.component("comp1").material("mat2").propertyGroup("def").func("nemiss").label("Piecewise 8");
    model.component("comp1").material("mat2").propertyGroup("def").func("nemiss").set("fununit", "");
    model.component("comp1").material("mat2").propertyGroup("def").func("nemiss").set("argunit", "");
    model.component("comp1").material("mat2").propertyGroup("def").addInput("temperature");
    model.component("comp1").material("mat2").propertyGroup("def").addInput("strainreferencetemperature");
    model.component("comp1").material("mat2").propertyGroup().create("ThermalExpansion", "Thermal expansion");
    model.component("comp1").material("mat2").propertyGroup("ThermalExpansion")
         .set("dL", "(dL(T[1/K])-dL(Tempref[1/K]))/(1+dL(Tempref[1/K]))");
    model.component("comp1").material("mat2").propertyGroup("ThermalExpansion")
         .set("dLIso", "(dL(T[1/K])-dL(Tempref[1/K]))/(1+dL(Tempref[1/K]))");
    model.component("comp1").material("mat2").propertyGroup("ThermalExpansion").func().create("dL", "Piecewise");
    model.component("comp1").material("mat2").propertyGroup("ThermalExpansion").func("dL").set("funcname", "dL");
    model.component("comp1").material("mat2").propertyGroup("ThermalExpansion").func("dL").set("arg", "T");
    model.component("comp1").material("mat2").propertyGroup("ThermalExpansion").func("dL").set("extrap", "constant");
    model.component("comp1").material("mat2").propertyGroup("ThermalExpansion").func("dL")
         .set("pieces", new String[][]{{"0.0", "80.0", "-5.465879E-4-1.25E-7*T^1-3.020833E-8*T^2+6.25E-10*T^3-2.604167E-12*T^4"}, {"80.0", "673.0", "-5.97183E-4-1.112134E-7*T^1+1.288373E-8*T^2-2.540265E-11*T^3+2.471846E-14*T^4-9.026049E-18*T^5"}});
    model.component("comp1").material("mat2").propertyGroup("ThermalExpansion").func("dL").label("Piecewise");
    model.component("comp1").material("mat2").propertyGroup("ThermalExpansion").func("dL").set("fununit", "");
    model.component("comp1").material("mat2").propertyGroup("ThermalExpansion").func("dL").set("argunit", "");
    model.component("comp1").material("mat2").propertyGroup("ThermalExpansion").addInput("temperature");
    model.component("comp1").material("mat2").propertyGroup("ThermalExpansion")
         .addInput("strainreferencetemperature");
    model.component("comp1").material("mat2").propertyGroup().create("Enu", "Young's modulus and Poisson's ratio");
    model.component("comp1").material("mat2").propertyGroup("Enu").set("youngsmodulus", "E(T[1/K])[Pa]");
    model.component("comp1").material("mat2").propertyGroup("Enu").set("poissonsratio", "nu(T[1/K])");
    model.component("comp1").material("mat2").propertyGroup("Enu").func().create("E", "Piecewise");
    model.component("comp1").material("mat2").propertyGroup("Enu").func("E").set("funcname", "E");
    model.component("comp1").material("mat2").propertyGroup("Enu").func("E").set("arg", "T");
    model.component("comp1").material("mat2").propertyGroup("Enu").func("E").set("extrap", "constant");
    model.component("comp1").material("mat2").propertyGroup("Enu").func("E")
         .set("pieces", new String[][]{{"293.0", "773.0", "6.069563E10+6408672.0*T^1"}});
    model.component("comp1").material("mat2").propertyGroup("Enu").func("E").label("Piecewise");
    model.component("comp1").material("mat2").propertyGroup("Enu").func("E").set("fununit", "");
    model.component("comp1").material("mat2").propertyGroup("Enu").func("E").set("argunit", "");
    model.component("comp1").material("mat2").propertyGroup("Enu").func().create("nu", "Piecewise");
    model.component("comp1").material("mat2").propertyGroup("Enu").func("nu").set("funcname", "nu");
    model.component("comp1").material("mat2").propertyGroup("Enu").func("nu").set("arg", "T");
    model.component("comp1").material("mat2").propertyGroup("Enu").func("nu").set("extrap", "constant");
    model.component("comp1").material("mat2").propertyGroup("Enu").func("nu")
         .set("pieces", new String[][]{{"293.0", "773.0", "0.2204121+1.722974E-5*T^1"}});
    model.component("comp1").material("mat2").propertyGroup("Enu").func("nu").label("Piecewise 1");
    model.component("comp1").material("mat2").propertyGroup("Enu").func("nu").set("fununit", "");
    model.component("comp1").material("mat2").propertyGroup("Enu").func("nu").set("argunit", "");
    model.component("comp1").material("mat2").propertyGroup("Enu").addInput("temperature");
    model.component("comp1").material("mat2").propertyGroup().create("KG", "Bulk modulus and shear modulus");
    model.component("comp1").material("mat2").propertyGroup("KG").set("G", "mu(T[1/K])[Pa]");
    model.component("comp1").material("mat2").propertyGroup("KG").set("K", "kappa(T[1/K])[Pa]");
    model.component("comp1").material("mat2").propertyGroup("KG").func().create("mu", "Piecewise");
    model.component("comp1").material("mat2").propertyGroup("KG").func("mu").set("funcname", "mu");
    model.component("comp1").material("mat2").propertyGroup("KG").func("mu").set("arg", "T");
    model.component("comp1").material("mat2").propertyGroup("KG").func("mu").set("extrap", "constant");
    model.component("comp1").material("mat2").propertyGroup("KG").func("mu")
         .set("pieces", new String[][]{{"293.0", "773.0", "2.487521E10+2240750.0*T^1"}});
    model.component("comp1").material("mat2").propertyGroup("KG").func("mu").label("Piecewise");
    model.component("comp1").material("mat2").propertyGroup("KG").func("mu").set("fununit", "");
    model.component("comp1").material("mat2").propertyGroup("KG").func("mu").set("argunit", "");
    model.component("comp1").material("mat2").propertyGroup("KG").func().create("kappa", "Piecewise");
    model.component("comp1").material("mat2").propertyGroup("KG").func("kappa").set("funcname", "kappa");
    model.component("comp1").material("mat2").propertyGroup("KG").func("kappa").set("arg", "T");
    model.component("comp1").material("mat2").propertyGroup("KG").func("kappa").set("extrap", "constant");
    model.component("comp1").material("mat2").propertyGroup("KG").func("kappa")
         .set("pieces", new String[][]{{"293.0", "773.0", "3.607632E10+6468087.0*T^1"}});
    model.component("comp1").material("mat2").propertyGroup("KG").func("kappa").label("Piecewise 1");
    model.component("comp1").material("mat2").propertyGroup("KG").func("kappa").set("fununit", "");
    model.component("comp1").material("mat2").propertyGroup("KG").func("kappa").set("argunit", "");
    model.component("comp1").material("mat2").propertyGroup("KG").addInput("temperature");
    model.component("comp1").material("mat2").set("family", "custom");
    model.component("comp1").material("mat2").set("lighting", "cooktorrance");
    model.component("comp1").material("mat2").set("specular", "custom");
    model.component("comp1").material("mat2").set("customspecular", new double[]{1, 1, 1});
    model.component("comp1").material("mat2").set("diffuse", "custom");
    model.component("comp1").material("mat2").set("customdiffuse", new double[]{1, 1, 1});
    model.component("comp1").material("mat2").set("ambient", "custom");
    model.component("comp1").material("mat2").set("customambient", new double[]{1, 1, 1});
    model.component("comp1").material("mat2").set("fresnel", 0.99);
    model.component("comp1").material("mat2").set("roughness", 0.02);
    model.component("comp1").material("mat2").set("shininess", 200);
    model.component("comp1").material("mat2").set("alpha", 1);

    model.component("comp1").physics("es").feature("pot1").selection().set(19);

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol1").attach("std1");

    model.result().create("pg1", "PlotGroup3D");
    model.result("pg1").label("Electric Potential (es)");
    model.result("pg1").set("solvertype", "none");
    model.result("pg1").set("frametype", "spatial");
    model.result("pg1").set("data", "dset1");
    model.result("pg1").feature().create("mslc1", "Multislice");
    model.result("pg1").feature("mslc1").set("solvertype", "none");
    model.result("pg1").feature("mslc1").set("colortable", "RainbowLight");
    model.result("pg1").feature("mslc1").set("data", "parent");

    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.component("comp1").geom("geom1").feature("wp1").active(false);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();
    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();
    model.component("comp1").view("view1").set("renderwireframe", true);
    model.component("comp1").view("view1").set("transparency", true);

    model.component("comp1").material("mat1").selection().set(2);

    model.component("comp1").view("view1").set("showgrid", true);
    model.component("comp1").view("view1").set("showaxisorientation", true);
    model.component("comp1").view("view1").set("renderwireframe", false);

    model.component("comp1").material("mat2").selection().all();
    model.component("comp1").material("mat2").selection().set(2);
    model.component("comp1").material("mat1").selection().set();
    model.component("comp1").material("mat1").selection().all();
    model.component("comp1").material("mat1").selection().set(1);
    model.component("comp1").material("mat2").propertyGroup("def").set("relpermittivity", new String[]{"4.6"});

    model.component("comp1").physics("es").feature("pot1").selection().all();
    model.component("comp1").physics("es").feature("pot1").selection().set(4, 8, 14, 15, 16, 17, 18);

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(6);
    model.component("comp1").view("view1").hideEntities("hide1").add(5);

    model.component("comp1").physics("es").feature("pot1").selection().set(8);

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").create("surf1", "Surface");
    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").create("slc1", "Slice");
    model.result("pg1").run();
    model.result("pg1").feature("slc1").set("quickxnumber", 1);
    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").feature("surf1").active(false);
    model.result("pg1").run();
    model.result("pg1").feature("surf1").active(true);
    model.result("pg1").run();
    model.result("pg1").feature("surf1").active(false);
    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").run();

    model.component("comp1").geom("geom1").feature("dif1").set("keep", true);
    model.component("comp1").geom("geom1").feature().duplicate("cyl4", "cyl1");
    model.component("comp1").geom("geom1").feature().move("cyl4", 4);
    model.component("comp1").geom("geom1").feature().move("cyl2", 3);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl4").set("r", 100);
    model.component("comp1").geom("geom1").feature("cyl4").set("h", 500);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl4").set("pos", new int[]{0, 0, -250});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl4").set("h", 600);
    model.component("comp1").geom("geom1").feature("cyl4").set("pos", new int[]{0, 0, -150});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run();
    model.component("comp1").geom("geom1").feature("dif1").set("keep", false);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run();

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.component("comp1").geom("geom1").feature().remove("wp1");

    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").feature("mslc1").active(false);
    model.result("pg1").run();

    model.component("comp1").physics("cpt").active(true);
    model.component("comp1").physics("cpt").create("pbeam1", "ParticleBeam", 2);
    model.component("comp1").physics("cpt").feature("pbeam1").set("N", 100);
    model.component("comp1").physics("cpt").feature().remove("pbeam1");
    model.component("comp1").physics("cpt").create("relg1", "ReleaseGrid", -1);
    model.component("comp1").physics("cpt").feature("relg1").set("InitialVelocity", "Expression");

    model.study().create("std2");
    model.study("std2").create("time", "Transient");
    model.study("std2").feature("time").activate("es", true);
    model.study("std2").feature("time").activate("cpt", true);

    model.sol().create("sol2");
    model.sol("sol2").study("std2");

    model.study("std2").feature("time").set("notlistsolnum", 1);
    model.study("std2").feature("time").set("notsolnum", "1");
    model.study("std2").feature("time").set("listsolnum", 1);
    model.study("std2").feature("time").set("solnum", "1");

    model.sol("sol2").create("st1", "StudyStep");
    model.sol("sol2").feature("st1").set("study", "std2");
    model.sol("sol2").feature("st1").set("studystep", "time");
    model.sol("sol2").create("v1", "Variables");
    model.sol("sol2").feature("v1").set("control", "time");
    model.sol("sol2").create("t1", "Time");
    model.sol("sol2").feature("t1").set("tlist", "range(0,0.1,1)");
    model.sol("sol2").feature("t1").set("plot", "off");
    model.sol("sol2").feature("t1").set("plotgroup", "pg1");
    model.sol("sol2").feature("t1").set("plotfreq", "tout");
    model.sol("sol2").feature("t1").set("probesel", "all");
    model.sol("sol2").feature("t1").set("probes", new String[]{});
    model.sol("sol2").feature("t1").set("probefreq", "tsteps");
    model.sol("sol2").feature("t1").set("rtol", 1.0E-5);
    model.sol("sol2").feature("t1").set("atolglobalvaluemethod", "factor");
    model.sol("sol2").feature("t1").set("tstepsgenalpha", "strict");
    model.sol("sol2").feature("t1").set("timemethod", "genalpha");
    model.sol("sol2").feature("t1").set("estrat", "exclude");
    model.sol("sol2").feature("t1").set("control", "time");
    model.sol("sol2").feature("t1").create("se1", "Segregated");
    model.sol("sol2").feature("t1").feature("se1").feature().remove("ssDef");
    model.sol("sol2").feature("t1").feature("se1").create("ss1", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("segvar", new String[]{"comp1_qcpt"});
    model.sol("sol2").feature("t1").create("i1", "Iterative");
    model.sol("sol2").feature("t1").feature("i1").set("linsolver", "gmres");
    model.sol("sol2").feature("t1").feature("i1").create("ja1", "Jacobi");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("linsolver", "i1");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").label("Charged Particle Tracing");
    model.sol("sol2").feature("t1").feature("se1").create("ss2", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("segvar", new String[]{"comp1_V"});
    model.sol("sol2").feature("t1").create("i2", "Iterative");
    model.sol("sol2").feature("t1").feature("i2").set("linsolver", "cg");
    model.sol("sol2").feature("t1").feature("i2").create("mg1", "Multigrid");
    model.sol("sol2").feature("t1").feature("i2").feature("mg1").set("prefun", "amg");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("linsolver", "i2");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").label("Electrostatics");
    model.sol("sol2").feature("t1").feature().remove("fcDef");
    model.sol("sol2").attach("std2");

    model.result().create("pg2", "PlotGroup3D");
    model.result("pg2").label("Electric Potential (es) 1");
    model.result("pg2").set("frametype", "spatial");
    model.result("pg2").set("data", "dset2");
    model.result("pg2").feature().create("mslc1", "Multislice");
    model.result("pg2").feature("mslc1").set("colortable", "RainbowLight");
    model.result("pg2").feature("mslc1").set("data", "parent");
    model.result().dataset().create("part1", "Particle");
    model.result().dataset("part1").set("solution", "sol2");
    model.result().dataset("part1").set("posdof", new String[]{"comp1.qx", "comp1.qy", "comp1.qz"});
    model.result().dataset("part1").set("geom", "geom1");
    model.result().dataset("part1").set("pgeom", "pgeom_cpt");
    model.result().dataset("part1").set("pgeomspec", "fromphysics");
    model.result().dataset("part1").set("physicsinterface", "cpt");
    model.result().create("pg3", "PlotGroup3D");
    model.result("pg3").set("data", "dset2");
    model.result("pg3").label("Particle Trajectories (cpt)");
    model.result("pg3").set("data", "part1");
    model.result("pg3").create("traj1", "ParticleTrajectories");
    model.result("pg3").feature("traj1").set("pointtype", "point");
    model.result("pg3").feature("traj1").set("linetype", "none");
    model.result("pg3").feature("traj1").create("col1", "Color");
    model.result("pg3").feature("traj1").feature("col1").set("expr", "cpt.V");

    model.sol("sol2").runAll();

    model.result("pg2").run();
    model.result("pg2").set("data", "dset2");
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 5, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 1, 0);
    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("relg1").setIndex("x0", 11, 2);

    model.sol("sol2").study("std2");

    model.study("std2").feature("time").set("notlistsolnum", 1);
    model.study("std2").feature("time").set("notsolnum", "1");
    model.study("std2").feature("time").set("listsolnum", 1);
    model.study("std2").feature("time").set("solnum", "1");

    model.sol("sol2").feature().remove("t1");
    model.sol("sol2").feature().remove("v1");
    model.sol("sol2").feature().remove("st1");
    model.sol("sol2").create("st1", "StudyStep");
    model.sol("sol2").feature("st1").set("study", "std2");
    model.sol("sol2").feature("st1").set("studystep", "time");
    model.sol("sol2").create("v1", "Variables");
    model.sol("sol2").feature("v1").set("control", "time");
    model.sol("sol2").create("t1", "Time");
    model.sol("sol2").feature("t1").set("tlist", "range(0,0.1,1)");
    model.sol("sol2").feature("t1").set("plot", "off");
    model.sol("sol2").feature("t1").set("plotgroup", "pg1");
    model.sol("sol2").feature("t1").set("plotfreq", "tout");
    model.sol("sol2").feature("t1").set("probesel", "all");
    model.sol("sol2").feature("t1").set("probes", new String[]{});
    model.sol("sol2").feature("t1").set("probefreq", "tsteps");
    model.sol("sol2").feature("t1").set("rtol", 1.0E-5);
    model.sol("sol2").feature("t1").set("atolglobalvaluemethod", "factor");
    model.sol("sol2").feature("t1").set("tstepsgenalpha", "strict");
    model.sol("sol2").feature("t1").set("timemethod", "genalpha");
    model.sol("sol2").feature("t1").set("estrat", "exclude");
    model.sol("sol2").feature("t1").set("control", "time");
    model.sol("sol2").feature("t1").create("se1", "Segregated");
    model.sol("sol2").feature("t1").feature("se1").feature().remove("ssDef");
    model.sol("sol2").feature("t1").feature("se1").create("ss1", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("segvar", new String[]{"comp1_qcpt"});
    model.sol("sol2").feature("t1").create("i1", "Iterative");
    model.sol("sol2").feature("t1").feature("i1").set("linsolver", "gmres");
    model.sol("sol2").feature("t1").feature("i1").create("ja1", "Jacobi");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("linsolver", "i1");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").label("Charged Particle Tracing");
    model.sol("sol2").feature("t1").feature("se1").create("ss2", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("segvar", new String[]{"comp1_V"});
    model.sol("sol2").feature("t1").create("i2", "Iterative");
    model.sol("sol2").feature("t1").feature("i2").set("linsolver", "cg");
    model.sol("sol2").feature("t1").feature("i2").create("mg1", "Multigrid");
    model.sol("sol2").feature("t1").feature("i2").feature("mg1").set("prefun", "amg");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("linsolver", "i2");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").label("Electrostatics");

    return model;
  }

  public static Model run3(Model model) {
    model.sol("sol2").feature("t1").feature().remove("fcDef");
    model.sol("sol2").attach("std2");
    model.sol("sol2").runAll();

    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 8, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 11, 0);
    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("relg1").setIndex("x0", 25, 2);

    model.sol("sol2").study("std2");

    model.study("std2").feature("time").set("notlistsolnum", 1);
    model.study("std2").feature("time").set("notsolnum", "1");
    model.study("std2").feature("time").set("listsolnum", 1);
    model.study("std2").feature("time").set("solnum", "1");

    model.sol("sol2").feature().remove("t1");
    model.sol("sol2").feature().remove("v1");
    model.sol("sol2").feature().remove("st1");
    model.sol("sol2").create("st1", "StudyStep");
    model.sol("sol2").feature("st1").set("study", "std2");
    model.sol("sol2").feature("st1").set("studystep", "time");
    model.sol("sol2").create("v1", "Variables");
    model.sol("sol2").feature("v1").set("control", "time");
    model.sol("sol2").create("t1", "Time");
    model.sol("sol2").feature("t1").set("tlist", "range(0,0.1,1)");
    model.sol("sol2").feature("t1").set("plot", "off");
    model.sol("sol2").feature("t1").set("plotgroup", "pg1");
    model.sol("sol2").feature("t1").set("plotfreq", "tout");
    model.sol("sol2").feature("t1").set("probesel", "all");
    model.sol("sol2").feature("t1").set("probes", new String[]{});
    model.sol("sol2").feature("t1").set("probefreq", "tsteps");
    model.sol("sol2").feature("t1").set("rtol", 1.0E-5);
    model.sol("sol2").feature("t1").set("atolglobalvaluemethod", "factor");
    model.sol("sol2").feature("t1").set("tstepsgenalpha", "strict");
    model.sol("sol2").feature("t1").set("timemethod", "genalpha");
    model.sol("sol2").feature("t1").set("estrat", "exclude");
    model.sol("sol2").feature("t1").set("control", "time");
    model.sol("sol2").feature("t1").create("se1", "Segregated");
    model.sol("sol2").feature("t1").feature("se1").feature().remove("ssDef");
    model.sol("sol2").feature("t1").feature("se1").create("ss1", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("segvar", new String[]{"comp1_qcpt"});
    model.sol("sol2").feature("t1").create("i1", "Iterative");
    model.sol("sol2").feature("t1").feature("i1").set("linsolver", "gmres");
    model.sol("sol2").feature("t1").feature("i1").create("ja1", "Jacobi");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("linsolver", "i1");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").label("Charged Particle Tracing");
    model.sol("sol2").feature("t1").feature("se1").create("ss2", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("segvar", new String[]{"comp1_V"});
    model.sol("sol2").feature("t1").create("i2", "Iterative");
    model.sol("sol2").feature("t1").feature("i2").set("linsolver", "cg");
    model.sol("sol2").feature("t1").feature("i2").create("mg1", "Multigrid");
    model.sol("sol2").feature("t1").feature("i2").feature("mg1").set("prefun", "amg");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("linsolver", "i2");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").label("Electrostatics");
    model.sol("sol2").feature("t1").feature().remove("fcDef");
    model.sol("sol2").attach("std2");
    model.sol("sol2").runAll();

    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 7, 0);
    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("pp1").set("Z", 1);
    model.component("comp1").physics("cpt").feature("pp1").set("mp", "1e-22");

    model.sol("sol2").study("std2");

    model.study("std2").feature("time").set("notlistsolnum", 1);
    model.study("std2").feature("time").set("notsolnum", "1");
    model.study("std2").feature("time").set("listsolnum", 1);
    model.study("std2").feature("time").set("solnum", "1");

    model.sol("sol2").feature().remove("t1");
    model.sol("sol2").feature().remove("v1");
    model.sol("sol2").feature().remove("st1");
    model.sol("sol2").create("st1", "StudyStep");
    model.sol("sol2").feature("st1").set("study", "std2");
    model.sol("sol2").feature("st1").set("studystep", "time");
    model.sol("sol2").create("v1", "Variables");
    model.sol("sol2").feature("v1").set("control", "time");
    model.sol("sol2").create("t1", "Time");
    model.sol("sol2").feature("t1").set("tlist", "range(0,0.1,1)");
    model.sol("sol2").feature("t1").set("plot", "off");
    model.sol("sol2").feature("t1").set("plotgroup", "pg1");
    model.sol("sol2").feature("t1").set("plotfreq", "tout");
    model.sol("sol2").feature("t1").set("probesel", "all");
    model.sol("sol2").feature("t1").set("probes", new String[]{});
    model.sol("sol2").feature("t1").set("probefreq", "tsteps");
    model.sol("sol2").feature("t1").set("rtol", 1.0E-5);
    model.sol("sol2").feature("t1").set("atolglobalvaluemethod", "factor");
    model.sol("sol2").feature("t1").set("tstepsgenalpha", "strict");
    model.sol("sol2").feature("t1").set("timemethod", "genalpha");
    model.sol("sol2").feature("t1").set("estrat", "exclude");
    model.sol("sol2").feature("t1").set("control", "time");
    model.sol("sol2").feature("t1").create("se1", "Segregated");
    model.sol("sol2").feature("t1").feature("se1").feature().remove("ssDef");
    model.sol("sol2").feature("t1").feature("se1").create("ss1", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("segvar", new String[]{"comp1_qcpt"});
    model.sol("sol2").feature("t1").create("i1", "Iterative");
    model.sol("sol2").feature("t1").feature("i1").set("linsolver", "gmres");
    model.sol("sol2").feature("t1").feature("i1").create("ja1", "Jacobi");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("linsolver", "i1");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").label("Charged Particle Tracing");
    model.sol("sol2").feature("t1").feature("se1").create("ss2", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("segvar", new String[]{"comp1_V"});
    model.sol("sol2").feature("t1").create("i2", "Iterative");
    model.sol("sol2").feature("t1").feature("i2").set("linsolver", "cg");
    model.sol("sol2").feature("t1").feature("i2").create("mg1", "Multigrid");
    model.sol("sol2").feature("t1").feature("i2").feature("mg1").set("prefun", "amg");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("linsolver", "i2");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").label("Electrostatics");
    model.sol("sol2").feature("t1").feature().remove("fcDef");
    model.sol("sol2").attach("std2");
    model.sol("sol2").runAll();

    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 1, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 11, 0);
    model.result("pg3").run();
    model.result("pg3").set("data", "dset2");
    model.result("pg3").setIndex("looplevel", 5, 0);
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").set("data", "part1");
    model.result("pg3").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.result("pg3").run();
    model.result("pg1").run();

    model.sol("sol2").study("std2");

    model.study("std2").feature("time").set("notlistsolnum", 1);
    model.study("std2").feature("time").set("notsolnum", "1");
    model.study("std2").feature("time").set("listsolnum", 1);
    model.study("std2").feature("time").set("solnum", "1");

    model.sol("sol2").feature().remove("t1");
    model.sol("sol2").feature().remove("v1");
    model.sol("sol2").feature().remove("st1");
    model.sol("sol2").create("st1", "StudyStep");
    model.sol("sol2").feature("st1").set("study", "std2");
    model.sol("sol2").feature("st1").set("studystep", "time");
    model.sol("sol2").create("v1", "Variables");
    model.sol("sol2").feature("v1").set("control", "time");
    model.sol("sol2").create("t1", "Time");
    model.sol("sol2").feature("t1").set("tlist", "range(0,0.1,1)");
    model.sol("sol2").feature("t1").set("plot", "off");
    model.sol("sol2").feature("t1").set("plotgroup", "pg1");
    model.sol("sol2").feature("t1").set("plotfreq", "tout");
    model.sol("sol2").feature("t1").set("probesel", "all");
    model.sol("sol2").feature("t1").set("probes", new String[]{});
    model.sol("sol2").feature("t1").set("probefreq", "tsteps");
    model.sol("sol2").feature("t1").set("rtol", 1.0E-5);
    model.sol("sol2").feature("t1").set("atolglobalvaluemethod", "factor");
    model.sol("sol2").feature("t1").set("tstepsgenalpha", "strict");
    model.sol("sol2").feature("t1").set("timemethod", "genalpha");
    model.sol("sol2").feature("t1").set("estrat", "exclude");
    model.sol("sol2").feature("t1").set("control", "time");
    model.sol("sol2").feature("t1").create("se1", "Segregated");
    model.sol("sol2").feature("t1").feature("se1").feature().remove("ssDef");
    model.sol("sol2").feature("t1").feature("se1").create("ss1", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("segvar", new String[]{"comp1_qcpt"});
    model.sol("sol2").feature("t1").create("i1", "Iterative");
    model.sol("sol2").feature("t1").feature("i1").set("linsolver", "gmres");
    model.sol("sol2").feature("t1").feature("i1").create("ja1", "Jacobi");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("linsolver", "i1");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").label("Charged Particle Tracing");
    model.sol("sol2").feature("t1").feature("se1").create("ss2", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("segvar", new String[]{"comp1_V"});
    model.sol("sol2").feature("t1").create("i2", "Iterative");
    model.sol("sol2").feature("t1").feature("i2").set("linsolver", "cg");
    model.sol("sol2").feature("t1").feature("i2").create("mg1", "Multigrid");
    model.sol("sol2").feature("t1").feature("i2").feature("mg1").set("prefun", "amg");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("linsolver", "i2");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").label("Electrostatics");
    model.sol("sol2").feature("t1").feature().remove("fcDef");
    model.sol("sol2").attach("std2");
    model.sol("sol2").runAll();

    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 1, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 11, 0);
    model.result("pg3").run();
    model.result("pg1").run();

    model.component("comp1").physics("cpt").feature("relg1").set("v0", new double[]{0, 0, 0.1});

    model.sol("sol2").study("std2");

    model.study("std2").feature("time").set("notlistsolnum", 1);
    model.study("std2").feature("time").set("notsolnum", "1");
    model.study("std2").feature("time").set("listsolnum", 1);
    model.study("std2").feature("time").set("solnum", "1");

    model.sol("sol2").feature().remove("t1");
    model.sol("sol2").feature().remove("v1");
    model.sol("sol2").feature().remove("st1");
    model.sol("sol2").create("st1", "StudyStep");
    model.sol("sol2").feature("st1").set("study", "std2");
    model.sol("sol2").feature("st1").set("studystep", "time");
    model.sol("sol2").create("v1", "Variables");
    model.sol("sol2").feature("v1").set("control", "time");
    model.sol("sol2").create("t1", "Time");
    model.sol("sol2").feature("t1").set("tlist", "range(0,0.1,1)");
    model.sol("sol2").feature("t1").set("plot", "off");
    model.sol("sol2").feature("t1").set("plotgroup", "pg1");
    model.sol("sol2").feature("t1").set("plotfreq", "tout");
    model.sol("sol2").feature("t1").set("probesel", "all");
    model.sol("sol2").feature("t1").set("probes", new String[]{});
    model.sol("sol2").feature("t1").set("probefreq", "tsteps");
    model.sol("sol2").feature("t1").set("rtol", 1.0E-5);
    model.sol("sol2").feature("t1").set("atolglobalvaluemethod", "factor");
    model.sol("sol2").feature("t1").set("tstepsgenalpha", "strict");
    model.sol("sol2").feature("t1").set("timemethod", "genalpha");
    model.sol("sol2").feature("t1").set("estrat", "exclude");
    model.sol("sol2").feature("t1").set("control", "time");
    model.sol("sol2").feature("t1").create("se1", "Segregated");
    model.sol("sol2").feature("t1").feature("se1").feature().remove("ssDef");
    model.sol("sol2").feature("t1").feature("se1").create("ss1", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("segvar", new String[]{"comp1_qcpt"});
    model.sol("sol2").feature("t1").create("i1", "Iterative");
    model.sol("sol2").feature("t1").feature("i1").set("linsolver", "gmres");
    model.sol("sol2").feature("t1").feature("i1").create("ja1", "Jacobi");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("linsolver", "i1");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").label("Charged Particle Tracing");
    model.sol("sol2").feature("t1").feature("se1").create("ss2", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("segvar", new String[]{"comp1_V"});
    model.sol("sol2").feature("t1").create("i2", "Iterative");
    model.sol("sol2").feature("t1").feature("i2").set("linsolver", "cg");
    model.sol("sol2").feature("t1").feature("i2").create("mg1", "Multigrid");
    model.sol("sol2").feature("t1").feature("i2").feature("mg1").set("prefun", "amg");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("linsolver", "i2");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").label("Electrostatics");
    model.sol("sol2").feature("t1").feature().remove("fcDef");
    model.sol("sol2").attach("std2");
    model.sol("sol2").runAll();

    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 3, 0);
    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("relg1").set("v0", new int[]{0, 0, 0});
    model.component("comp1").physics("es").feature("pot1").set("V0", -10000);

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.sol("sol2").study("std2");

    model.study("std2").feature("time").set("notlistsolnum", 1);
    model.study("std2").feature("time").set("notsolnum", "1");
    model.study("std2").feature("time").set("listsolnum", 1);
    model.study("std2").feature("time").set("solnum", "1");

    model.sol("sol2").feature().remove("t1");
    model.sol("sol2").feature().remove("v1");
    model.sol("sol2").feature().remove("st1");
    model.sol("sol2").create("st1", "StudyStep");
    model.sol("sol2").feature("st1").set("study", "std2");
    model.sol("sol2").feature("st1").set("studystep", "time");
    model.sol("sol2").create("v1", "Variables");
    model.sol("sol2").feature("v1").set("control", "time");
    model.sol("sol2").create("t1", "Time");
    model.sol("sol2").feature("t1").set("tlist", "range(0,0.1,1)");
    model.sol("sol2").feature("t1").set("plot", "off");
    model.sol("sol2").feature("t1").set("plotgroup", "pg1");
    model.sol("sol2").feature("t1").set("plotfreq", "tout");
    model.sol("sol2").feature("t1").set("probesel", "all");
    model.sol("sol2").feature("t1").set("probes", new String[]{});
    model.sol("sol2").feature("t1").set("probefreq", "tsteps");
    model.sol("sol2").feature("t1").set("rtol", 1.0E-5);
    model.sol("sol2").feature("t1").set("atolglobalvaluemethod", "factor");
    model.sol("sol2").feature("t1").set("tstepsgenalpha", "strict");
    model.sol("sol2").feature("t1").set("timemethod", "genalpha");
    model.sol("sol2").feature("t1").set("estrat", "exclude");
    model.sol("sol2").feature("t1").set("control", "time");
    model.sol("sol2").feature("t1").create("se1", "Segregated");
    model.sol("sol2").feature("t1").feature("se1").feature().remove("ssDef");
    model.sol("sol2").feature("t1").feature("se1").create("ss1", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("segvar", new String[]{"comp1_qcpt"});
    model.sol("sol2").feature("t1").create("i1", "Iterative");
    model.sol("sol2").feature("t1").feature("i1").set("linsolver", "gmres");
    model.sol("sol2").feature("t1").feature("i1").create("ja1", "Jacobi");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("linsolver", "i1");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").label("Charged Particle Tracing");
    model.sol("sol2").feature("t1").feature("se1").create("ss2", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("segvar", new String[]{"comp1_V"});
    model.sol("sol2").feature("t1").create("i2", "Iterative");
    model.sol("sol2").feature("t1").feature("i2").set("linsolver", "cg");
    model.sol("sol2").feature("t1").feature("i2").create("mg1", "Multigrid");
    model.sol("sol2").feature("t1").feature("i2").feature("mg1").set("prefun", "amg");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("linsolver", "i2");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").label("Electrostatics");
    model.sol("sol2").feature("t1").feature().remove("fcDef");
    model.sol("sol2").attach("std2");
    model.sol("sol2").runAll();

    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 9, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 2, 0);
    model.result("pg3").run();
    model.result("pg1").run();

    model.component("comp1").physics("cpt").feature("relg1").setIndex("x0", 250, 2);

    model.sol("sol2").study("std2");

    model.study("std2").feature("time").set("notlistsolnum", 1);
    model.study("std2").feature("time").set("notsolnum", "1");
    model.study("std2").feature("time").set("listsolnum", 1);
    model.study("std2").feature("time").set("solnum", "1");

    model.sol("sol2").feature().remove("t1");
    model.sol("sol2").feature().remove("v1");
    model.sol("sol2").feature().remove("st1");
    model.sol("sol2").create("st1", "StudyStep");
    model.sol("sol2").feature("st1").set("study", "std2");
    model.sol("sol2").feature("st1").set("studystep", "time");
    model.sol("sol2").create("v1", "Variables");
    model.sol("sol2").feature("v1").set("control", "time");
    model.sol("sol2").create("t1", "Time");
    model.sol("sol2").feature("t1").set("tlist", "range(0,0.1,1)");
    model.sol("sol2").feature("t1").set("plot", "off");
    model.sol("sol2").feature("t1").set("plotgroup", "pg1");
    model.sol("sol2").feature("t1").set("plotfreq", "tout");
    model.sol("sol2").feature("t1").set("probesel", "all");
    model.sol("sol2").feature("t1").set("probes", new String[]{});
    model.sol("sol2").feature("t1").set("probefreq", "tsteps");
    model.sol("sol2").feature("t1").set("rtol", 1.0E-5);
    model.sol("sol2").feature("t1").set("atolglobalvaluemethod", "factor");
    model.sol("sol2").feature("t1").set("tstepsgenalpha", "strict");
    model.sol("sol2").feature("t1").set("timemethod", "genalpha");
    model.sol("sol2").feature("t1").set("estrat", "exclude");
    model.sol("sol2").feature("t1").set("control", "time");
    model.sol("sol2").feature("t1").create("se1", "Segregated");
    model.sol("sol2").feature("t1").feature("se1").feature().remove("ssDef");
    model.sol("sol2").feature("t1").feature("se1").create("ss1", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("segvar", new String[]{"comp1_qcpt"});
    model.sol("sol2").feature("t1").create("i1", "Iterative");
    model.sol("sol2").feature("t1").feature("i1").set("linsolver", "gmres");
    model.sol("sol2").feature("t1").feature("i1").create("ja1", "Jacobi");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("linsolver", "i1");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").label("Charged Particle Tracing");
    model.sol("sol2").feature("t1").feature("se1").create("ss2", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("segvar", new String[]{"comp1_V"});
    model.sol("sol2").feature("t1").create("i2", "Iterative");
    model.sol("sol2").feature("t1").feature("i2").set("linsolver", "cg");
    model.sol("sol2").feature("t1").feature("i2").create("mg1", "Multigrid");
    model.sol("sol2").feature("t1").feature("i2").feature("mg1").set("prefun", "amg");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("linsolver", "i2");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").label("Electrostatics");
    model.sol("sol2").feature("t1").feature().remove("fcDef");
    model.sol("sol2").attach("std2");
    model.sol("sol2").runAll();

    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 8, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 11, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 1, 0);
    model.result("pg3").run();
    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("relg1").setIndex("x0", 280, 2);

    model.sol("sol2").study("std2");

    model.study("std2").feature("time").set("notlistsolnum", 1);
    model.study("std2").feature("time").set("notsolnum", "1");
    model.study("std2").feature("time").set("listsolnum", 1);
    model.study("std2").feature("time").set("solnum", "1");

    model.sol("sol2").feature().remove("t1");
    model.sol("sol2").feature().remove("v1");
    model.sol("sol2").feature().remove("st1");
    model.sol("sol2").create("st1", "StudyStep");
    model.sol("sol2").feature("st1").set("study", "std2");
    model.sol("sol2").feature("st1").set("studystep", "time");
    model.sol("sol2").create("v1", "Variables");
    model.sol("sol2").feature("v1").set("control", "time");
    model.sol("sol2").create("t1", "Time");
    model.sol("sol2").feature("t1").set("tlist", "range(0,0.1,1)");
    model.sol("sol2").feature("t1").set("plot", "off");
    model.sol("sol2").feature("t1").set("plotgroup", "pg1");
    model.sol("sol2").feature("t1").set("plotfreq", "tout");
    model.sol("sol2").feature("t1").set("probesel", "all");
    model.sol("sol2").feature("t1").set("probes", new String[]{});
    model.sol("sol2").feature("t1").set("probefreq", "tsteps");
    model.sol("sol2").feature("t1").set("rtol", 1.0E-5);
    model.sol("sol2").feature("t1").set("atolglobalvaluemethod", "factor");
    model.sol("sol2").feature("t1").set("tstepsgenalpha", "strict");
    model.sol("sol2").feature("t1").set("timemethod", "genalpha");
    model.sol("sol2").feature("t1").set("estrat", "exclude");
    model.sol("sol2").feature("t1").set("control", "time");
    model.sol("sol2").feature("t1").create("se1", "Segregated");
    model.sol("sol2").feature("t1").feature("se1").feature().remove("ssDef");
    model.sol("sol2").feature("t1").feature("se1").create("ss1", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("segvar", new String[]{"comp1_qcpt"});
    model.sol("sol2").feature("t1").create("i1", "Iterative");
    model.sol("sol2").feature("t1").feature("i1").set("linsolver", "gmres");
    model.sol("sol2").feature("t1").feature("i1").create("ja1", "Jacobi");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("linsolver", "i1");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").label("Charged Particle Tracing");
    model.sol("sol2").feature("t1").feature("se1").create("ss2", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("segvar", new String[]{"comp1_V"});
    model.sol("sol2").feature("t1").create("i2", "Iterative");
    model.sol("sol2").feature("t1").feature("i2").set("linsolver", "cg");
    model.sol("sol2").feature("t1").feature("i2").create("mg1", "Multigrid");
    model.sol("sol2").feature("t1").feature("i2").feature("mg1").set("prefun", "amg");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("linsolver", "i2");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").label("Electrostatics");
    model.sol("sol2").feature("t1").feature().remove("fcDef");
    model.sol("sol2").attach("std2");
    model.sol("sol2").runAll();

    model.result("pg2").run();

    model.label("t5ett.mph");

    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 7, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 11, 0);
    model.result("pg3").run();

    model.component("comp1").physics("cpt").prop("EquationForm").setIndex("form", "Transient", 0);
    model.component("comp1").physics("cpt").prop("EquationForm").setIndex("form", "Automatic", 0);
    model.component("comp1").physics("cpt").create("ef1", "ElectricForce", 3);
    model.component("comp1").physics("cpt").feature("ef1").selection().all();

    model.sol("sol2").study("std2");

    model.study("std2").feature("time").set("notlistsolnum", 1);
    model.study("std2").feature("time").set("notsolnum", "1");
    model.study("std2").feature("time").set("listsolnum", 1);
    model.study("std2").feature("time").set("solnum", "1");

    model.sol("sol2").feature().remove("t1");
    model.sol("sol2").feature().remove("v1");
    model.sol("sol2").feature().remove("st1");
    model.sol("sol2").create("st1", "StudyStep");
    model.sol("sol2").feature("st1").set("study", "std2");
    model.sol("sol2").feature("st1").set("studystep", "time");
    model.sol("sol2").create("v1", "Variables");
    model.sol("sol2").feature("v1").set("control", "time");
    model.sol("sol2").create("t1", "Time");
    model.sol("sol2").feature("t1").set("tlist", "range(0,0.1,1)");
    model.sol("sol2").feature("t1").set("plot", "off");
    model.sol("sol2").feature("t1").set("plotgroup", "pg1");
    model.sol("sol2").feature("t1").set("plotfreq", "tout");
    model.sol("sol2").feature("t1").set("probesel", "all");
    model.sol("sol2").feature("t1").set("probes", new String[]{});
    model.sol("sol2").feature("t1").set("probefreq", "tsteps");
    model.sol("sol2").feature("t1").set("rtol", 1.0E-5);
    model.sol("sol2").feature("t1").set("atolglobalvaluemethod", "factor");
    model.sol("sol2").feature("t1").set("tstepsgenalpha", "strict");
    model.sol("sol2").feature("t1").set("timemethod", "genalpha");
    model.sol("sol2").feature("t1").set("estrat", "exclude");
    model.sol("sol2").feature("t1").set("control", "time");
    model.sol("sol2").feature("t1").create("se1", "Segregated");
    model.sol("sol2").feature("t1").feature("se1").feature().remove("ssDef");
    model.sol("sol2").feature("t1").feature("se1").create("ss1", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("segvar", new String[]{"comp1_qcpt"});
    model.sol("sol2").feature("t1").create("i1", "Iterative");
    model.sol("sol2").feature("t1").feature("i1").set("linsolver", "gmres");
    model.sol("sol2").feature("t1").feature("i1").create("ja1", "Jacobi");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("linsolver", "i1");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").label("Charged Particle Tracing");
    model.sol("sol2").feature("t1").feature("se1").create("ss2", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("segvar", new String[]{"comp1_V"});
    model.sol("sol2").feature("t1").create("i2", "Iterative");
    model.sol("sol2").feature("t1").feature("i2").set("linsolver", "cg");
    model.sol("sol2").feature("t1").feature("i2").create("mg1", "Multigrid");
    model.sol("sol2").feature("t1").feature("i2").feature("mg1").set("prefun", "amg");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("linsolver", "i2");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").label("Electrostatics");
    model.sol("sol2").feature("t1").feature().remove("fcDef");
    model.sol("sol2").attach("std2");
    model.sol("sol2").runAll();

    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 1, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 11, 0);
    model.result("pg3").run();

    model.sol("sol2").study("std2");

    model.study("std2").feature("time").set("notlistsolnum", 1);
    model.study("std2").feature("time").set("notsolnum", "1");
    model.study("std2").feature("time").set("listsolnum", 1);
    model.study("std2").feature("time").set("solnum", "1");

    model.sol("sol2").feature().remove("t1");
    model.sol("sol2").feature().remove("v1");
    model.sol("sol2").feature().remove("st1");
    model.sol("sol2").create("st1", "StudyStep");
    model.sol("sol2").feature("st1").set("study", "std2");
    model.sol("sol2").feature("st1").set("studystep", "time");
    model.sol("sol2").create("v1", "Variables");
    model.sol("sol2").feature("v1").set("control", "time");
    model.sol("sol2").create("t1", "Time");
    model.sol("sol2").feature("t1").set("tlist", "range(0,0.1,1)");
    model.sol("sol2").feature("t1").set("plot", "off");
    model.sol("sol2").feature("t1").set("plotgroup", "pg1");
    model.sol("sol2").feature("t1").set("plotfreq", "tout");
    model.sol("sol2").feature("t1").set("probesel", "all");
    model.sol("sol2").feature("t1").set("probes", new String[]{});

    return model;
  }

  public static Model run4(Model model) {
    model.sol("sol2").feature("t1").set("probefreq", "tsteps");
    model.sol("sol2").feature("t1").set("rtol", 1.0E-5);
    model.sol("sol2").feature("t1").set("atolglobalvaluemethod", "factor");
    model.sol("sol2").feature("t1").set("tstepsgenalpha", "strict");
    model.sol("sol2").feature("t1").set("timemethod", "genalpha");
    model.sol("sol2").feature("t1").set("estrat", "exclude");
    model.sol("sol2").feature("t1").set("control", "time");
    model.sol("sol2").feature("t1").create("se1", "Segregated");
    model.sol("sol2").feature("t1").feature("se1").feature().remove("ssDef");
    model.sol("sol2").feature("t1").feature("se1").create("ss1", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("segvar", new String[]{"comp1_qcpt"});
    model.sol("sol2").feature("t1").create("i1", "Iterative");
    model.sol("sol2").feature("t1").feature("i1").set("linsolver", "gmres");
    model.sol("sol2").feature("t1").feature("i1").create("ja1", "Jacobi");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("linsolver", "i1");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").label("Charged Particle Tracing");
    model.sol("sol2").feature("t1").feature("se1").create("ss2", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("segvar", new String[]{"comp1_V"});
    model.sol("sol2").feature("t1").create("i2", "Iterative");
    model.sol("sol2").feature("t1").feature("i2").set("linsolver", "cg");
    model.sol("sol2").feature("t1").feature("i2").create("mg1", "Multigrid");
    model.sol("sol2").feature("t1").feature("i2").feature("mg1").set("prefun", "amg");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("linsolver", "i2");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").label("Electrostatics");
    model.sol("sol2").feature("t1").feature().remove("fcDef");
    model.sol("sol2").attach("std2");
    model.sol("sol2").runAll();

    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 4, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 1, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 11, 0);
    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature().move("ef1", 2);
    model.component("comp1").physics("cpt").feature("ef1").set("E_src", "root.comp1.es.Ex");

    model.sol("sol2").study("std2");

    model.study("std2").feature("time").set("notlistsolnum", 1);
    model.study("std2").feature("time").set("notsolnum", "1");
    model.study("std2").feature("time").set("listsolnum", 1);
    model.study("std2").feature("time").set("solnum", "1");

    model.sol("sol2").feature().remove("t1");
    model.sol("sol2").feature().remove("v1");
    model.sol("sol2").feature().remove("st1");
    model.sol("sol2").create("st1", "StudyStep");
    model.sol("sol2").feature("st1").set("study", "std2");
    model.sol("sol2").feature("st1").set("studystep", "time");
    model.sol("sol2").create("v1", "Variables");
    model.sol("sol2").feature("v1").set("control", "time");
    model.sol("sol2").create("t1", "Time");
    model.sol("sol2").feature("t1").set("tlist", "range(0,0.1,1)");
    model.sol("sol2").feature("t1").set("plot", "off");
    model.sol("sol2").feature("t1").set("plotgroup", "pg1");
    model.sol("sol2").feature("t1").set("plotfreq", "tout");
    model.sol("sol2").feature("t1").set("probesel", "all");
    model.sol("sol2").feature("t1").set("probes", new String[]{});
    model.sol("sol2").feature("t1").set("probefreq", "tsteps");
    model.sol("sol2").feature("t1").set("rtol", 1.0E-5);
    model.sol("sol2").feature("t1").set("atolglobalvaluemethod", "factor");
    model.sol("sol2").feature("t1").set("tstepsgenalpha", "strict");
    model.sol("sol2").feature("t1").set("timemethod", "genalpha");
    model.sol("sol2").feature("t1").set("estrat", "exclude");
    model.sol("sol2").feature("t1").set("control", "time");
    model.sol("sol2").feature("t1").create("se1", "Segregated");
    model.sol("sol2").feature("t1").feature("se1").feature().remove("ssDef");
    model.sol("sol2").feature("t1").feature("se1").create("ss1", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("segvar", new String[]{"comp1_qcpt"});
    model.sol("sol2").feature("t1").create("i1", "Iterative");
    model.sol("sol2").feature("t1").feature("i1").set("linsolver", "gmres");
    model.sol("sol2").feature("t1").feature("i1").create("ja1", "Jacobi");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("linsolver", "i1");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").label("Charged Particle Tracing");
    model.sol("sol2").feature("t1").feature("se1").create("ss2", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("segvar", new String[]{"comp1_V"});
    model.sol("sol2").feature("t1").create("i2", "Iterative");
    model.sol("sol2").feature("t1").feature("i2").set("linsolver", "cg");
    model.sol("sol2").feature("t1").feature("i2").create("mg1", "Multigrid");
    model.sol("sol2").feature("t1").feature("i2").feature("mg1").set("prefun", "amg");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("linsolver", "i2");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").label("Electrostatics");
    model.sol("sol2").feature("t1").feature().remove("fcDef");
    model.sol("sol2").attach("std2");
    model.sol("sol2").runAll();

    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 1, 0);
    model.result("pg3").run();

    model.component("comp1").physics("es").feature("pot1").set("V0", -300);

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.component("comp1").physics("cpt").feature("relg1").setIndex("x0", 25, 2);

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.sol("sol2").study("std2");

    model.study("std2").feature("time").set("notlistsolnum", 1);
    model.study("std2").feature("time").set("notsolnum", "1");
    model.study("std2").feature("time").set("listsolnum", 1);
    model.study("std2").feature("time").set("solnum", "1");

    model.sol("sol2").feature().remove("t1");
    model.sol("sol2").feature().remove("v1");
    model.sol("sol2").feature().remove("st1");
    model.sol("sol2").create("st1", "StudyStep");
    model.sol("sol2").feature("st1").set("study", "std2");
    model.sol("sol2").feature("st1").set("studystep", "time");
    model.sol("sol2").create("v1", "Variables");
    model.sol("sol2").feature("v1").set("control", "time");
    model.sol("sol2").create("t1", "Time");
    model.sol("sol2").feature("t1").set("tlist", "range(0,0.1,1)");
    model.sol("sol2").feature("t1").set("plot", "off");
    model.sol("sol2").feature("t1").set("plotgroup", "pg1");
    model.sol("sol2").feature("t1").set("plotfreq", "tout");
    model.sol("sol2").feature("t1").set("probesel", "all");
    model.sol("sol2").feature("t1").set("probes", new String[]{});
    model.sol("sol2").feature("t1").set("probefreq", "tsteps");
    model.sol("sol2").feature("t1").set("rtol", 1.0E-5);
    model.sol("sol2").feature("t1").set("atolglobalvaluemethod", "factor");
    model.sol("sol2").feature("t1").set("tstepsgenalpha", "strict");
    model.sol("sol2").feature("t1").set("timemethod", "genalpha");
    model.sol("sol2").feature("t1").set("estrat", "exclude");
    model.sol("sol2").feature("t1").set("control", "time");
    model.sol("sol2").feature("t1").create("se1", "Segregated");
    model.sol("sol2").feature("t1").feature("se1").feature().remove("ssDef");
    model.sol("sol2").feature("t1").feature("se1").create("ss1", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("segvar", new String[]{"comp1_qcpt"});
    model.sol("sol2").feature("t1").create("i1", "Iterative");
    model.sol("sol2").feature("t1").feature("i1").set("linsolver", "gmres");
    model.sol("sol2").feature("t1").feature("i1").create("ja1", "Jacobi");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("linsolver", "i1");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").label("Charged Particle Tracing");
    model.sol("sol2").feature("t1").feature("se1").create("ss2", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("segvar", new String[]{"comp1_V"});
    model.sol("sol2").feature("t1").create("i2", "Iterative");
    model.sol("sol2").feature("t1").feature("i2").set("linsolver", "cg");
    model.sol("sol2").feature("t1").feature("i2").create("mg1", "Multigrid");
    model.sol("sol2").feature("t1").feature("i2").feature("mg1").set("prefun", "amg");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("linsolver", "i2");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").label("Electrostatics");
    model.sol("sol2").feature("t1").feature().remove("fcDef");
    model.sol("sol2").attach("std2");

    model.component("comp1").physics("cpt").feature("relg1").setIndex("x0", 15, 2);
    model.component("comp1").physics("cpt").feature("ef1").set("UsePPR", true);
    model.component("comp1").physics("cpt").prop("MaximumSecondary").setIndex("MaximumSecondary", 100, 0);

    model.sol("sol2").study("std2");

    model.study("std2").feature("time").set("notlistsolnum", 1);
    model.study("std2").feature("time").set("notsolnum", "1");
    model.study("std2").feature("time").set("listsolnum", 1);
    model.study("std2").feature("time").set("solnum", "1");

    model.sol("sol2").feature().remove("t1");
    model.sol("sol2").feature().remove("v1");
    model.sol("sol2").feature().remove("st1");
    model.sol("sol2").create("st1", "StudyStep");
    model.sol("sol2").feature("st1").set("study", "std2");
    model.sol("sol2").feature("st1").set("studystep", "time");
    model.sol("sol2").create("v1", "Variables");
    model.sol("sol2").feature("v1").set("control", "time");
    model.sol("sol2").create("t1", "Time");
    model.sol("sol2").feature("t1").set("tlist", "range(0,0.1,1)");
    model.sol("sol2").feature("t1").set("plot", "off");
    model.sol("sol2").feature("t1").set("plotgroup", "pg1");
    model.sol("sol2").feature("t1").set("plotfreq", "tout");
    model.sol("sol2").feature("t1").set("probesel", "all");
    model.sol("sol2").feature("t1").set("probes", new String[]{});
    model.sol("sol2").feature("t1").set("probefreq", "tsteps");
    model.sol("sol2").feature("t1").set("rtol", 1.0E-5);
    model.sol("sol2").feature("t1").set("atolglobalvaluemethod", "factor");
    model.sol("sol2").feature("t1").set("tstepsgenalpha", "strict");
    model.sol("sol2").feature("t1").set("timemethod", "genalpha");
    model.sol("sol2").feature("t1").set("estrat", "exclude");
    model.sol("sol2").feature("t1").set("control", "time");
    model.sol("sol2").feature("t1").create("se1", "Segregated");
    model.sol("sol2").feature("t1").feature("se1").feature().remove("ssDef");
    model.sol("sol2").feature("t1").feature("se1").create("ss1", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("segvar", new String[]{"comp1_qcpt"});
    model.sol("sol2").feature("t1").create("i1", "Iterative");
    model.sol("sol2").feature("t1").feature("i1").set("linsolver", "gmres");
    model.sol("sol2").feature("t1").feature("i1").create("ja1", "Jacobi");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("linsolver", "i1");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").label("Charged Particle Tracing");
    model.sol("sol2").feature("t1").feature("se1").create("ss2", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("segvar", new String[]{"comp1_V"});
    model.sol("sol2").feature("t1").create("i2", "Iterative");
    model.sol("sol2").feature("t1").feature("i2").set("linsolver", "cg");
    model.sol("sol2").feature("t1").feature("i2").create("mg1", "Multigrid");
    model.sol("sol2").feature("t1").feature("i2").feature("mg1").set("prefun", "amg");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("linsolver", "i2");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").label("Electrostatics");
    model.sol("sol2").feature("t1").feature().remove("fcDef");
    model.sol("sol2").attach("std2");

    model.component("comp1").physics("cpt").create("pbeam1", "ParticleBeam", 2);
    model.component("comp1").physics("cpt").feature("pbeam1").set("N", 100);
    model.component("comp1").physics("cpt").feature("pbeam1").selection().all();
    model.component("comp1").physics("cpt").feature("pbeam1").selection().set(13, 14, 15, 16, 20, 21);

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(6);

    model.component("comp1").physics("cpt").feature("pbeam1").selection().set(10, 13, 14, 15, 16, 20, 21);

    model.component("comp1").view("view1").hideEntities("hide1").add(10);
    model.component("comp1").view("view1").set("hidestatus", "hide");
    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();
    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(6);
    model.component("comp1").view("view1").hideEntities("hide1").add(5);
    model.component("comp1").view("view1").hideEntities("hide1").add(9);
    model.component("comp1").view("view1").hideEntities("hide1").add(18);

    model.component("comp1").physics("cpt").feature("pbeam1").selection().all();
    model.component("comp1").physics("cpt").feature("pbeam1").selection()
         .set(5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24);

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.component("comp1").physics("cpt").feature("pbeam1").selection().set();
    model.component("comp1").physics("cpt").feature("relg1").active(false);
    model.component("comp1").physics("cpt").feature("pbeam1").selection().all();
    model.component("comp1").physics("cpt").feature("pbeam1").set("BeamOrientation", "Upright");
    model.component("comp1").physics("cpt").feature("pbeam1").selection().set(11);

    model.sol("sol2").study("std2");

    model.study("std2").feature("time").set("notlistsolnum", 1);
    model.study("std2").feature("time").set("notsolnum", "1");
    model.study("std2").feature("time").set("listsolnum", 1);
    model.study("std2").feature("time").set("solnum", "1");

    model.sol("sol2").feature().remove("t1");
    model.sol("sol2").feature().remove("v1");
    model.sol("sol2").feature().remove("st1");
    model.sol("sol2").create("st1", "StudyStep");
    model.sol("sol2").feature("st1").set("study", "std2");
    model.sol("sol2").feature("st1").set("studystep", "time");
    model.sol("sol2").create("v1", "Variables");
    model.sol("sol2").feature("v1").set("control", "time");
    model.sol("sol2").create("t1", "Time");
    model.sol("sol2").feature("t1").set("tlist", "range(0,0.1,1)");
    model.sol("sol2").feature("t1").set("plot", "off");
    model.sol("sol2").feature("t1").set("plotgroup", "pg1");
    model.sol("sol2").feature("t1").set("plotfreq", "tout");
    model.sol("sol2").feature("t1").set("probesel", "all");
    model.sol("sol2").feature("t1").set("probes", new String[]{});
    model.sol("sol2").feature("t1").set("probefreq", "tsteps");
    model.sol("sol2").feature("t1").set("rtol", 1.0E-5);
    model.sol("sol2").feature("t1").set("atolglobalvaluemethod", "factor");
    model.sol("sol2").feature("t1").set("tstepsgenalpha", "strict");
    model.sol("sol2").feature("t1").set("timemethod", "genalpha");
    model.sol("sol2").feature("t1").set("estrat", "exclude");
    model.sol("sol2").feature("t1").set("control", "time");
    model.sol("sol2").feature("t1").create("se1", "Segregated");
    model.sol("sol2").feature("t1").feature("se1").feature().remove("ssDef");
    model.sol("sol2").feature("t1").feature("se1").create("ss1", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("segvar", new String[]{"comp1_qcpt"});
    model.sol("sol2").feature("t1").create("i1", "Iterative");
    model.sol("sol2").feature("t1").feature("i1").set("linsolver", "gmres");
    model.sol("sol2").feature("t1").feature("i1").create("ja1", "Jacobi");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("linsolver", "i1");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").label("Charged Particle Tracing");
    model.sol("sol2").feature("t1").feature("se1").create("ss2", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("segvar", new String[]{"comp1_V"});
    model.sol("sol2").feature("t1").create("i2", "Iterative");
    model.sol("sol2").feature("t1").feature("i2").set("linsolver", "cg");
    model.sol("sol2").feature("t1").feature("i2").create("mg1", "Multigrid");
    model.sol("sol2").feature("t1").feature("i2").feature("mg1").set("prefun", "amg");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("linsolver", "i2");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").label("Electrostatics");
    model.sol("sol2").feature("t1").feature().remove("fcDef");
    model.sol("sol2").attach("std2");
    model.sol("sol2").runAll();

    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 1, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 11, 0);
    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("pbeam1").set("BeamSymmetry", "Symmetric");
    model.component("comp1").physics("cpt").feature("pbeam1").set("BeamOrientation", "Upright");

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(6);
    model.component("comp1").view("view1").set("scenelight", true);
    model.component("comp1").view("view1").set("renderwireframe", true);
    model.component("comp1").view("view1").camera().set("projection", "orthographic");

    model.component("comp1").physics("cpt").feature("pbeam1").selection().all();
    model.component("comp1").physics("cpt").feature("pbeam1").selection()
         .set(2, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24);
    model.component("comp1").physics("cpt").feature("pbeam1").set("BeamOrientation", "Upright");
    model.component("comp1").physics("cpt").feature("pbeam1").set("ReverseDirection", true);
    model.component("comp1").physics("cpt").feature("pbeam1").selection()
         .set(9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24);

    model.component("comp1").view("view1").hideEntities("hide1").add(18);
    model.component("comp1").view("view1").hideEntities("hide1").add(19);
    model.component("comp1").view("view1").hideEntities("hide1").add(5);

    model.component("comp1").physics("cpt").feature("pbeam1").selection()
         .set(10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24);

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.component("comp1").physics("cpt").feature("pbeam1").selection().all();

    model.component("comp1").view("view1").camera().set("projection", "perspective");

    model.component("comp1").physics("cpt").feature("pbeam1").selection().set(16);

    model.sol("sol2").study("std2");

    model.study("std2").feature("time").set("notlistsolnum", 1);
    model.study("std2").feature("time").set("notsolnum", "1");
    model.study("std2").feature("time").set("listsolnum", 1);
    model.study("std2").feature("time").set("solnum", "1");

    model.sol("sol2").feature().remove("t1");
    model.sol("sol2").feature().remove("v1");
    model.sol("sol2").feature().remove("st1");
    model.sol("sol2").create("st1", "StudyStep");
    model.sol("sol2").feature("st1").set("study", "std2");
    model.sol("sol2").feature("st1").set("studystep", "time");
    model.sol("sol2").create("v1", "Variables");
    model.sol("sol2").feature("v1").set("control", "time");
    model.sol("sol2").create("t1", "Time");
    model.sol("sol2").feature("t1").set("tlist", "range(0,0.1,1)");
    model.sol("sol2").feature("t1").set("plot", "off");
    model.sol("sol2").feature("t1").set("plotgroup", "pg1");
    model.sol("sol2").feature("t1").set("plotfreq", "tout");
    model.sol("sol2").feature("t1").set("probesel", "all");
    model.sol("sol2").feature("t1").set("probes", new String[]{});
    model.sol("sol2").feature("t1").set("probefreq", "tsteps");
    model.sol("sol2").feature("t1").set("rtol", 1.0E-5);
    model.sol("sol2").feature("t1").set("atolglobalvaluemethod", "factor");
    model.sol("sol2").feature("t1").set("tstepsgenalpha", "strict");
    model.sol("sol2").feature("t1").set("timemethod", "genalpha");
    model.sol("sol2").feature("t1").set("estrat", "exclude");
    model.sol("sol2").feature("t1").set("control", "time");
    model.sol("sol2").feature("t1").create("se1", "Segregated");
    model.sol("sol2").feature("t1").feature("se1").feature().remove("ssDef");
    model.sol("sol2").feature("t1").feature("se1").create("ss1", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("segvar", new String[]{"comp1_qcpt"});
    model.sol("sol2").feature("t1").create("i1", "Iterative");
    model.sol("sol2").feature("t1").feature("i1").set("linsolver", "gmres");
    model.sol("sol2").feature("t1").feature("i1").create("ja1", "Jacobi");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("linsolver", "i1");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").label("Charged Particle Tracing");
    model.sol("sol2").feature("t1").feature("se1").create("ss2", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("segvar", new String[]{"comp1_V"});
    model.sol("sol2").feature("t1").create("i2", "Iterative");
    model.sol("sol2").feature("t1").feature("i2").set("linsolver", "cg");
    model.sol("sol2").feature("t1").feature("i2").create("mg1", "Multigrid");
    model.sol("sol2").feature("t1").feature("i2").feature("mg1").set("prefun", "amg");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("linsolver", "i2");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").label("Electrostatics");
    model.sol("sol2").feature("t1").feature().remove("fcDef");
    model.sol("sol2").attach("std2");

    model.component("comp1").physics("cpt").feature("pbeam1").set("N", 1);

    model.sol("sol2").study("std2");

    model.study("std2").feature("time").set("notlistsolnum", 1);
    model.study("std2").feature("time").set("notsolnum", "1");
    model.study("std2").feature("time").set("listsolnum", 1);
    model.study("std2").feature("time").set("solnum", "1");

    model.sol("sol2").feature().remove("t1");
    model.sol("sol2").feature().remove("v1");
    model.sol("sol2").feature().remove("st1");
    model.sol("sol2").create("st1", "StudyStep");
    model.sol("sol2").feature("st1").set("study", "std2");
    model.sol("sol2").feature("st1").set("studystep", "time");
    model.sol("sol2").create("v1", "Variables");
    model.sol("sol2").feature("v1").set("control", "time");
    model.sol("sol2").create("t1", "Time");
    model.sol("sol2").feature("t1").set("tlist", "range(0,0.1,1)");
    model.sol("sol2").feature("t1").set("plot", "off");
    model.sol("sol2").feature("t1").set("plotgroup", "pg1");
    model.sol("sol2").feature("t1").set("plotfreq", "tout");
    model.sol("sol2").feature("t1").set("probesel", "all");
    model.sol("sol2").feature("t1").set("probes", new String[]{});
    model.sol("sol2").feature("t1").set("probefreq", "tsteps");
    model.sol("sol2").feature("t1").set("rtol", 1.0E-5);
    model.sol("sol2").feature("t1").set("atolglobalvaluemethod", "factor");
    model.sol("sol2").feature("t1").set("tstepsgenalpha", "strict");
    model.sol("sol2").feature("t1").set("timemethod", "genalpha");
    model.sol("sol2").feature("t1").set("estrat", "exclude");
    model.sol("sol2").feature("t1").set("control", "time");
    model.sol("sol2").feature("t1").create("se1", "Segregated");
    model.sol("sol2").feature("t1").feature("se1").feature().remove("ssDef");
    model.sol("sol2").feature("t1").feature("se1").create("ss1", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("segvar", new String[]{"comp1_qcpt"});
    model.sol("sol2").feature("t1").create("i1", "Iterative");
    model.sol("sol2").feature("t1").feature("i1").set("linsolver", "gmres");
    model.sol("sol2").feature("t1").feature("i1").create("ja1", "Jacobi");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").set("linsolver", "i1");
    model.sol("sol2").feature("t1").feature("se1").feature("ss1").label("Charged Particle Tracing");
    model.sol("sol2").feature("t1").feature("se1").create("ss2", "SegregatedStep");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("segvar", new String[]{"comp1_V"});
    model.sol("sol2").feature("t1").create("i2", "Iterative");
    model.sol("sol2").feature("t1").feature("i2").set("linsolver", "cg");
    model.sol("sol2").feature("t1").feature("i2").create("mg1", "Multigrid");
    model.sol("sol2").feature("t1").feature("i2").feature("mg1").set("prefun", "amg");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").set("linsolver", "i2");
    model.sol("sol2").feature("t1").feature("se1").feature("ss2").label("Electrostatics");
    model.sol("sol2").feature("t1").feature().remove("fcDef");
    model.sol("sol2").attach("std2");
    model.sol("sol2").feature("t1").feature("i1").set("maxlinit", 1000);
    model.sol("sol2").feature("t1").feature("i2").set("maxlinit", 1000);

    model.component("comp1").physics("cpt").feature("pbeam1").set("BeamPosition", "FromCoordinates");
    model.component("comp1").physics("cpt").feature("pbeam1").set("rcb", new int[]{0, 0, 11});

    model.sol("sol2").runAll();

    model.result("pg2").run();

    model.component("comp1").physics("cpt").feature("pbeam1").set("N", 100);

    model.sol("sol2").runAll();

    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 1, 0);
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("pbeam1").set("rcb", new int[]{0, 0, 10});

    model.sol("sol2").runAll();

    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 7, 0);
    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature().duplicate("pbeam2", "pbeam1");
    model.component("comp1").physics("cpt").feature("pbeam1").active(false);
    model.component("comp1").physics("cpt").feature("pbeam2").selection().set();
    model.component("comp1").physics("cpt").feature("pbeam2").selection().all();
    model.component("comp1").physics("cpt").feature("pbeam2").selection().set(11);
    model.component("comp1").physics("cpt").feature("pbeam2").set("BeamPosition", "CentroidOfSelection");
    model.component("comp1").physics("cpt").feature("pbeam2").active(false);
    model.component("comp1").physics("cpt").create("inl1", "Inlet", 2);
    model.component("comp1").physics("cpt").feature("inl1").active(false);
    model.component("comp1").physics("cpt").feature("relg1").active(true);
    model.component("comp1").physics("cpt").feature("relg1").setIndex("x0", 250, 2);

    model.sol("sol2").runAll();

    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 4, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 1, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 2, 0);
    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("relg1").setIndex("x0", 200, 2);

    return model;
  }

  public static Model run5(Model model) {

    model.sol("sol2").runAll();

    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 1, 0);
    model.result("pg3").run();

    model.study("std2").feature("time").set("tlist", "range(0,0.01,0.1)");

    model.component("comp1").physics("cpt").feature("relg1").setIndex("x0", 250, 2);

    model.study("std2").feature("time").set("tlist", "range(0,1e-7,1e-6)");

    model.sol("sol2").runAll();

    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 5, 0);
    model.result("pg3").run();

    model.study("std2").feature("time").set("tlist", "range(0,1e-6,1e-5)");

    model.sol("sol2").runAll();

    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 11, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 6, 0);
    model.result("pg3").run();

    model.study("std2").feature("time").set("tlist", "range(0,1e-5,1e-4)");

    model.sol("sol2").runAll();

    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 10, 0);
    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("relg1").setIndex("x0", 15, 2);

    model.sol("sol2").runAll();

    model.result("pg2").run();

    model.component("comp1").physics("cpt").feature("relg1").active(false);
    model.component("comp1").physics("cpt").feature("pbeam1").active(true);

    model.sol("sol2").runAll();

    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 2, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 1, 0);
    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("pbeam1").set("BeamPosition", "CentroidOfSelection");

    model.sol("sol2").runAll();

    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 7, 0);
    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("pbeam1").set("N", 10);
    model.component("comp1").physics("cpt").feature("pbeam1").set("twbeta0", "100[nm]");
    model.component("comp1").physics("cpt").feature("pbeam1").set("e1rms", "100[nm]");

    model.sol("sol2").runAll();

    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 11, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 1, 0);
    model.result("pg3").run();
    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("pbeam1").set("N", 100);

    model.sol("sol2").runAll();

    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 11, 0);
    model.result("pg3").run();

    model.study("std2").feature("time").set("tlist", "range(0,1e-5,1e-3)");

    model.sol("sol2").runAll();

    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 101, 0);
    model.result("pg3").run();

    model.component("comp1").physics("cpt").create("inl2", "Inlet", 2);
    model.component("comp1").physics("cpt").feature("inl2").set("InitialPosition", "Density");
    model.component("comp1").physics("cpt").feature("inl2").set("N", 10);
    model.component("comp1").physics("cpt").feature("inl2").set("ReleaseDistributionAccuracyOrder", 1);
    model.component("comp1").physics("cpt").feature("inl2").selection().all();
    model.component("comp1").physics("cpt").feature("inl2").selection().set(16);
    model.component("comp1").physics("cpt").feature("pbeam1").active(false);
    model.component("comp1").physics("cpt").feature("inl2").set("InitialPosition", "MeshBased");

    model.sol("sol2").runAll();

    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 9, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 100, 0);
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 32, 0);
    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("inl2").set("InitialPosition", "ProjectedPlaneGrid");

    model.sol("sol2").runAll();

    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 100, 0);
    model.result("pg3").run();

    model.component("comp1").geom("geom1").feature("cyl2").set("r", 0.05);
    model.component("comp1").geom("geom1").runPre("fin");

    model.sol("sol2").runAll();

    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").run();

    model.component("comp1").geom("geom1").run("fin");

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.sol("sol2").runAll();

    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 101, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 40, 0);
    model.result("pg3").run();

    model.component("comp1").geom("geom1").feature("cyl2").set("pos", new int[]{0, 0, 75});
    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").feature("cyl2").set("r", 1);
    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").feature().duplicate("cyl5", "cyl2");
    model.component("comp1").geom("geom1").feature("cyl5").set("r", 25);
    model.component("comp1").geom("geom1").feature("cyl5").set("pos", new int[]{0, 0, 100});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature().duplicate("cyl6", "cyl5");
    model.component("comp1").geom("geom1").feature("cyl6").set("r", 5);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("cyl6");
    model.component("comp1").geom("geom1").create("dif2", "Difference");

    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4");
    model.component("comp1").view("view1").hideObjects("hide1").add("dif1");

    model.component("comp1").geom("geom1").feature("dif2").selection("input").set("cyl5");
    model.component("comp1").geom("geom1").feature("dif2").selection("input2").set("cyl6");
    model.component("comp1").geom("geom1").run("fin");

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(3);

    model.component("comp1").material("mat1").selection().set(1, 2, 3, 4);

    model.component("comp1").physics("es").feature().duplicate("pot2", "pot1");
    model.component("comp1").physics("es").feature("pot2").selection().set(12, 15);
    model.component("comp1").physics("es").feature("pot1").active(false);
    model.component("comp1").physics("es").feature("pot2").selection().set(13, 14, 15, 16, 17, 18, 26, 27, 30, 31);

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();
    model.result("pg2").run();

    model.component("comp1").view("view1").set("transparency", false);
    model.component("comp1").view("view1").set("scenelight", true);
    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.result("pg2").run();
    model.result("pg1").run();
    model.result("pg2").run();
    model.result("pg2").active(false);
    model.result("pg2").run();
    model.result("pg1").run();

    model.component("comp1").physics("cpt").feature("inl2").set("N", 2);

    model.study("std2").feature("time").set("tlist", "range(0,1e-7,1e-6)");

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.study("std2").feature("time").set("tlist", "range(0,1e-6,1e-5)");

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 11, 0);
    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("inl2").set("N", 10);

    model.result("pg1").run();
    model.result("pg3").run();

    model.study("std2").feature("time").set("tlist", "range(0,1e-6,1e-4)");

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 73, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 2, 0);
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").feature("traj1").set("linetype", "line");
    model.result("pg3").feature("traj1").set("interpolation", "uniform");
    model.result("pg3").run();
    model.result("pg2").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 99, 0);
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").feature("traj1").set("pointtype", "none");
    model.result("pg3").run();
    model.result("pg3").feature("traj1").set("pointtype", "arrow");
    model.result("pg3").run();
    model.result("pg3").feature("traj1").set("arrowscaleactive", true);
    model.result("pg3").feature("traj1").set("arrowscale", 0.02);
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").feature("traj1").set("pointtype", "point");
    model.result("pg3").run();
    model.result("pg3").feature("traj1").set("sphereradiusscaleactive", true);
    model.result("pg3").feature("traj1").set("sphereradiusscale", 10);
    model.result("pg3").run();
    model.result("pg3").feature("traj1").set("pointradiusexpr", "0.01");
    model.result("pg3").run();
    model.result("pg3").feature("traj1").set("pointradiusexpr", "0.1");
    model.result("pg3").run();

    model.component("comp1").geom("geom1").feature("cyl5").set("pos", new int[]{0, 0, 80});
    model.component("comp1").geom("geom1").feature("cyl6").set("pos", new int[]{0, 0, 80});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl6").set("pos", new int[]{0, 0, 90});
    model.component("comp1").geom("geom1").feature("cyl5").set("pos", new int[]{0, 0, 90});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run();

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(3);

    model.component("comp1").physics("cpt").create("wall2", "Wall", 2);
    model.component("comp1").physics("cpt").feature("wall2").selection().set(13, 14, 15, 16, 17, 18, 26, 27, 30, 31);

    model.study("std2").feature("time").set("tlist", "range(0,1e-6,1e-3)");

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.component("comp1").physics("cpt").feature("inl2").set("N", 100);

    model.study("std2").feature("time").setIndex("activate", false, 1);
    model.study("std2").feature("time").set("usesol", true);
    model.study("std2").feature("time").set("notsolmethod", "sol");
    model.study("std2").feature("time").set("notstudy", "std1");

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.component("comp1").geom("geom1").feature("cyl2").set("h", 40);
    model.component("comp1").geom("geom1").feature("cyl2").set("r", 0.5);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl2").set("pos", new int[]{0, 0, 50});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl5").set("r", 32.5);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl5").set("pos", new int[]{0, 0, 95});
    model.component("comp1").geom("geom1").feature("cyl6").set("pos", new int[]{0, 0, 95});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl6").set("h", 9);
    model.component("comp1").geom("geom1").feature("cyl5").set("h", 9);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature().duplicate("cyl7", "cyl5");
    model.component("comp1").geom("geom1").feature().duplicate("cyl8", "cyl6");
    model.component("comp1").geom("geom1").feature("cyl7").set("r", 15);
    model.component("comp1").geom("geom1").feature("cyl7").set("h", 5);
    model.component("comp1").geom("geom1").feature("cyl8").set("r", 20);
    model.component("comp1").geom("geom1").feature("cyl8").set("h", 5);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("cyl8");
    model.component("comp1").geom("geom1").create("dif3", "Difference");

    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4");
    model.component("comp1").view("view1").hideObjects("hide1").add("dif1");

    model.component("comp1").geom("geom1").feature("dif3").selection("input").set("cyl8");
    model.component("comp1").geom("geom1").feature("dif3").selection("input2").set("cyl7");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("dif3");
    model.component("comp1").geom("geom1").create("dif4", "Difference");
    model.component("comp1").geom("geom1").feature("dif4").selection("input").set("dif2");
    model.component("comp1").geom("geom1").feature("dif4").selection("input2").set("dif3");
    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").feature().duplicate("cyl9", "cyl7");
    model.component("comp1").geom("geom1").feature().duplicate("cyl10", "cyl8");
    model.component("comp1").geom("geom1").feature("cyl9").set("r", 12);
    model.component("comp1").geom("geom1").feature("cyl10").set("r", 13);
    model.component("comp1").geom("geom1").feature("cyl10").set("pos", new int[]{0, 0, 104});
    model.component("comp1").geom("geom1").feature("cyl9").set("pos", new int[]{0, 0, 104});
    model.component("comp1").geom("geom1").run("cyl10");
    model.component("comp1").geom("geom1").create("dif5", "Difference");
    model.component("comp1").geom("geom1").feature("dif5").selection("input").set("cyl10");
    model.component("comp1").geom("geom1").feature("dif5").selection("input2").set("cyl9");
    model.component("comp1").geom("geom1").run("dif5");
    model.component("comp1").geom("geom1").create("uni1", "Union");
    model.component("comp1").geom("geom1").feature("uni1").selection("input").set("dif4", "dif5");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();
    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(3);

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");
    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();
    model.result("pg1").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.result("pg1").run();

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(3);

    model.component("comp1").physics("es").feature("pot2").selection()
         .set(13, 14, 15, 16, 17, 22, 25, 29, 30, 31, 39, 44, 47, 52);

    model.component("comp1").selection().create("sel1", "Explicit");
    model.component("comp1").selection("sel1").geom(2);
    model.component("comp1").selection("sel1").label("Explicit 1");
    model.component("comp1").selection("sel1").set(13, 14, 15, 16, 17, 22, 25, 29, 30, 31, 39, 44, 47, 52);

    model.component("comp1").physics("es").feature("pot2").selection().named("sel1");

    model.component("comp1").selection().create("uni1", "Union");
    model.component("comp1").selection("uni1").set("input", new String[]{});
    model.component("comp1").selection().create("adj1", "Adjacent");
    model.component("comp1").selection("adj1").set("input", new String[]{"uni1"});
    model.component("comp1").selection("adj1").set("interior", true);
    model.component("comp1").selection("adj1").set("input", new String[]{"uni1"});
    model.component("comp1").selection().remove("sel1");
    model.component("comp1").selection().remove("uni1");
    model.component("comp1").selection().remove("adj1");

    model.component("comp1").geom("geom1").run("fin");

    model.component("comp1").selection().create("adj1", "Adjacent");
    model.component("comp1").selection("adj1").set("interior", true);
    model.component("comp1").selection("adj1").set("color", "8");
    model.component("comp1").selection("adj1").set("input", new String[]{});
    model.component("comp1").selection("adj1").set("entitydim", 3);

    model.component("comp1").physics("es").feature().duplicate("pot3", "pot2");
    model.component("comp1").physics("es").feature("pot2").active(false);
    model.component("comp1").physics("es").feature("pot3").selection().named("adj1");

    model.component("comp1").selection("adj1").set("entitydim", 2);
    model.component("comp1").selection().create("sel1", "Explicit");
    model.component("comp1").selection("sel1").geom("geom1", 2);
    model.component("comp1").selection("sel1").set(15);
    model.component("comp1").selection("sel1").all();
    model.component("comp1").selection("sel1").geom("geom1", 2);
    model.component("comp1").selection("sel1")
         .set(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55);
    model.component("comp1").selection("sel1").set("groupcontang", false);
    model.component("comp1").selection("sel1").set();
    model.component("comp1").selection("sel1").geom("geom1", 2, 1, new String[]{"exterior"});
    model.component("comp1").selection("sel1").set(15);
    model.component("comp1").selection("sel1").geom("geom1", 2, 1, new String[]{"exterior", "interior"});
    model.component("comp1").selection("sel1").set(15);

    model.component("comp1").geom("geom1").run("fin");

    model.component("comp1").physics("es").feature("pot3").selection().set();
    model.component("comp1").physics("es").feature("pot3").selection().all();
    model.component("comp1").physics("es").feature("pot3").selection().named("adj1");

    model.component("comp1").selection("adj1").set("entitydim", 1);
    model.component("comp1").selection().create("sel2", "Explicit");
    model.component("comp1").selection("sel2").set(4);
    model.component("comp1").selection().remove("sel1");
    model.component("comp1").selection().remove("adj1");
    model.component("comp1").selection("sel2").geom("geom1", 3, 2, new String[]{"exterior"});
    model.component("comp1").selection("sel2").set(4);
    model.component("comp1").selection("sel2").geom("geom1", 3, 2, new String[]{"exterior", "interior"});
    model.component("comp1").selection("sel2").set(4);

    model.component("comp1").physics("es").feature("pot3").selection().named("sel2");

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.result("pg1").run();

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(3);

    model.component("comp1").selection("sel2").set(4, 5);

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");

    return model;
  }

  public static Model run6(Model model) {
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.result("pg2").run();
    model.result("pg1").run();
    model.result("pg3").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.component("comp1").physics("es").feature("pot3").set("V0", -150);

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("inl2").set("InitialPosition", "Density");

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("inl2").active(false);
    model.component("comp1").physics("cpt").feature("pbeam1").active(true);

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("pbeam1").set("N", 1000);

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 976, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 106, 0);
    model.result("pg3").run();
    model.result("pg3").run();
    model.result().table().create("evl3", "Table");
    model.result().table("evl3").comments("Interactive 3D values");
    model.result().table("evl3").label("Evaluation 3D");
    model.result().table("evl3")
         .addRow(new double[]{11.562900104255245, -5.871908772994855, 139.4573626034703, 321.89260300858086}, new double[]{0, 0, 0, 0});

    model.component("comp1").mesh("mesh1").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();
    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(3);

    model.component("comp1").mesh("mesh1").autoMeshSize(4);
    model.component("comp1").mesh("mesh1").run();
    model.component("comp1").mesh("mesh1").autoMeshSize(3);
    model.component("comp1").mesh("mesh1").run();

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.result("pg1").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result().table("evl3")
         .addRow(new double[]{0.9852488503058535, -9.84326268739108, 144.65233369724055, 372.3593303246031}, new double[]{0, 0, 0, 0});
    model.result("pg3").setIndex("looplevel", 944, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 982, 0);
    model.result("pg3").run();

    model.component("comp1").physics("es").feature("pot3").active(false);

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 342, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 123, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 75, 0);
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").feature("traj1").set("sphereradiusscale", 1);
    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("pbeam1")
         .set("TransverseVelocityDistributionSpecification", "SpecifyPhaseSpaceEllipseDimensions");
    model.component("comp1").physics("cpt").feature("pbeam1").set("xm", "50[nm]");
    model.component("comp1").physics("cpt").feature("pbeam1").set("xmp", 0.01);

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("pbeam1").set("xmp", 0.1);

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("pbeam1").set("xmp", 0.2);

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 100, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 119, 0);
    model.result("pg3").run();

    model.component("comp1").view("view1").camera().set("projection", "orthographic");

    model.component("comp1").physics("cpt").feature("pbeam1").set("N", 10000);

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("pbeam1").set("N", 1000);
    model.component("comp1").physics("es").feature("pot3").active(true);

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.component("comp1").geom("geom1").run("uni1");
    model.component("comp1").geom("geom1").create("cone1", "Cone");
    model.component("comp1").geom("geom1").feature("cone1").set("specifytop", "radius");
    model.component("comp1").geom("geom1").feature().move("cone1", 4);
    model.component("comp1").geom("geom1").feature("cone1").set("r", 0.5);
    model.component("comp1").geom("geom1").feature("cyl2").set("h", 30);
    model.component("comp1").geom("geom1").feature("cone1").set("h", 10);
    model.component("comp1").geom("geom1").feature("cone1").set("rtop", 0.1);
    model.component("comp1").geom("geom1").feature("cone1").set("pos", new int[]{0, 0, 80});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run();

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(3);

    model.component("comp1").material("mat2").selection().set(6, 7);

    model.component("comp1").physics("cpt").feature("wall2").selection().named("sel2");
    model.component("comp1").physics("cpt").feature("pbeam1").selection().set(38);

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.result("pg1").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("pbeam1").set("xmp", 0.5);

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 1001, 0);
    model.result("pg3").run();

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(39);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(40);
    model.component("comp1").view("view1").hideEntities("hide1").add(5);
    model.component("comp1").view("view1").hideEntities("hide1").add(41);
    model.component("comp1").view("view1").hideEntities("hide1").add(9);

    model.component("comp1").mesh("mesh1").autoMeshSize(2);
    model.component("comp1").mesh("mesh1").run();

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.component("comp1").geom("geom1").run("uni1");
    model.component("comp1").geom("geom1").create("arr1", "Array");

    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4");
    model.component("comp1").view("view1").hideObjects("hide1").add("dif1");

    model.component("comp1").geom("geom1").feature("arr1").selection("input").set("uni1");
    model.component("comp1").geom("geom1").feature("arr1").set("displ", new double[]{0, 0, 11.23});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("arr1").set("fullsize", new int[]{1, 1, 2});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();
    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(3);

    model.component("comp1").material("mat1").selection().set(1, 2, 3, 4, 5, 6, 7, 8);

    model.component("comp1").mesh("mesh1").run();

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();
    model.result("pg3").run();
    model.result("pg1").run();
    model.result("pg3").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.component("comp1").geom("geom1").feature("arr1").set("fullsize", new int[]{1, 1, 5});
    model.component("comp1").geom("geom1").run("fin");

    model.component("comp1").mesh("mesh1").run();

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").feature("traj1").set("sphereradiusscaleactive", false);
    model.result("pg3").feature("traj1").set("pointradiusexpr", "1");
    model.result("pg3").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.result("pg3").run();

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(139);

    model.component("comp1").physics("cpt").create("wall3", "Wall", 2);

    model.component("comp1").view("view1").hideEntities("hide1").add(4);
    model.component("comp1").view("view1").hideEntities("hide1").add(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);

    return model;
  }

  public static Model run7(Model model) {
    model.component("comp1").view("view1").hideEntities("hide1").add(224);
    model.component("comp1").view("view1").hideEntities("hide1").add(140);
    model.component("comp1").view("view1").hideEntities("hide1").add(5);
    model.component("comp1").view("view1").hideEntities("hide1").add(223);
    model.component("comp1").view("view1").hideEntities("hide1").add(6);

    model.component("comp1").physics("cpt").feature("wall3").selection().set(7, 8, 9, 10, 141, 222);

    model.component("comp1").view("view1").hideEntities("hide1").add(222);
    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();
    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(224);
    model.component("comp1").view("view1").hideEntities("hide1").add(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(139);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);

    model.component("comp1").physics("cpt").feature("wall3").selection().set(5, 6, 7, 8, 9, 10, 140, 141, 222, 223);

    model.component("comp1").view("view1").set("hidestatus", "hide");
    model.component("comp1").view("view1").hideEntities("hide1").add(7);

    model.component("comp1").physics("cpt").feature("wall3").selection()
         .set(5, 6, 7, 8, 9, 10, 11, 140, 141, 222, 223);

    model.component("comp1").view("view1").hideEntities("hide1").add(8);

    model.component("comp1").physics("cpt").feature("wall3").selection()
         .set(5, 6, 7, 8, 9, 10, 11, 12, 140, 141, 222, 223);

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.component("comp1").geom("geom1").feature("arr1").set("fullsize", new int[]{1, 1, 1});
    model.component("comp1").geom("geom1").run("fin");

    model.component("comp1").mesh("mesh1").run();

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(60);
    model.component("comp1").view("view1").hideEntities("hide1").add(39);
    model.component("comp1").view("view1").hideEntities("hide1").add(40);
    model.component("comp1").view("view1").hideEntities("hide1").add(59);

    model.result("pg3").run();
    model.result("pg1").run();

    model.component("comp1").geom("geom1").feature("arr1").set("selresult", true);
    model.component("comp1").geom("geom1").feature("arr1").set("fullsize", new int[]{1, 1, 2});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("arr1").set("color", "6");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("arr1");
    model.component("comp1").geom("geom1").create("copy1", "Copy");
    model.component("comp1").geom("geom1").feature("copy1").set("displz", 11.23);

    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4");
    model.component("comp1").view("view1").hideObjects("hide1").add("dif1");

    model.component("comp1").geom("geom1").feature("copy1").selection("input").set("arr1(1,1,1)");
    model.component("comp1").geom("geom1").feature("arr1").active(false);
    model.component("comp1").geom("geom1").run("fin");

    model.component("comp1").view("view1").hideEntities().create("hide2");
    model.component("comp1").view("view1").hideEntities("hide2").geom(3);
    model.component("comp1").view("view1").hideEntities("hide2").add(1);
    model.component("comp1").view("view1").hideEntities("hide2").add(2);
    model.component("comp1").view("view1").hideEntities("hide2").add(3);

    model.component("comp1").physics("es").feature().duplicate("pot4", "pot3");
    model.component("comp1").physics("es").feature("pot4").selection().geom("geom1", 2);
    model.component("comp1").physics("es").feature("pot4").selection().set();

    model.component("comp1").selection().create("sel3", "Explicit");
    model.component("comp1").selection("sel3").set(5, 8);

    model.component("comp1").geom("geom1").feature("cyl8").set("r", 15);
    model.component("comp1").geom("geom1").feature("cyl7").set("r", 10);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();
    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(3);

    model.component("comp1").geom("geom1").runPre("uni1");

    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4");
    model.component("comp1").view("view1").hideObjects("hide1").add("dif1");
    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();
    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(3);

    model.component("comp1").selection("sel3").geom("geom1", 3, 2, new String[]{"exterior"});
    model.component("comp1").selection("sel3").set(5, 7);
    model.component("comp1").selection("sel3").geom("geom1", 3, 2, new String[]{"exterior", "interior"});
    model.component("comp1").selection("sel3").set(5, 7);

    model.component("comp1").physics("es").feature("pot4").selection().named("sel3");
    model.component("comp1").physics("es").feature("pot3").set("V0", -100);
    model.component("comp1").physics("cpt").feature().duplicate("wall4", "wall2");
    model.component("comp1").physics("cpt").feature().move("wall4", 9);
    model.component("comp1").physics("cpt").feature("wall4").selection().named("sel3");

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");

    model.component("comp1").material("mat1").selection().all();

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.result("pg1").run();
    model.result("pg3").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.component("comp1").geom("geom1").feature().duplicate("cyl11", "cyl10");
    model.component("comp1").geom("geom1").feature().move("cyl11", 20);
    model.component("comp1").geom("geom1").feature("cyl11").label("MCP Face");
    model.component("comp1").geom("geom1").feature("cyl11").set("r", 20);
    model.component("comp1").geom("geom1").feature("cyl11").set("pos", new int[]{0, 0, 125});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl11").set("pos", new int[]{0, 0, 150});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run();

    model.component("comp1").material().create("mat3", "Common");
    model.component("comp1").material("mat3").label("Leaded 1 [solid]");
    model.component("comp1").material("mat3").info().create("Composition");
    model.component("comp1").material("mat3").info("Composition").body("80.0 PbO, 20.0 SiO2 (wt%)");
    model.component("comp1").material("mat3").propertyGroup("def").set("thermalconductivity", "k(T[1/K])[W/(m*K)]");
    model.component("comp1").material("mat3").propertyGroup("def").func().create("k", "Piecewise");
    model.component("comp1").material("mat3").propertyGroup("def").func("k").set("funcname", "k");
    model.component("comp1").material("mat3").propertyGroup("def").func("k").set("arg", "T");
    model.component("comp1").material("mat3").propertyGroup("def").func("k").set("extrap", "constant");
    model.component("comp1").material("mat3").propertyGroup("def").func("k")
         .set("pieces", new String[][]{{"78.0", "353.0", "0.211875+0.001550097*T^1-2.75811E-6*T^2+4.074399E-9*T^3"}});
    model.component("comp1").material("mat3").propertyGroup("def").func("k").label("Piecewise");
    model.component("comp1").material("mat3").propertyGroup("def").func("k").set("fununit", "");
    model.component("comp1").material("mat3").propertyGroup("def").func("k").set("argunit", "");
    model.component("comp1").material("mat3").propertyGroup("def").addInput("temperature");
    model.component("comp1").material("mat3").set("family", "custom");
    model.component("comp1").material("mat3").set("lighting", "cooktorrance");
    model.component("comp1").material("mat3").set("specular", "custom");
    model.component("comp1").material("mat3").set("customspecular", new double[]{1, 1, 1});
    model.component("comp1").material("mat3").set("diffuse", "custom");
    model.component("comp1").material("mat3").set("customdiffuse", new double[]{1, 1, 1});
    model.component("comp1").material("mat3").set("ambient", "custom");
    model.component("comp1").material("mat3").set("customambient", new double[]{1, 1, 1});
    model.component("comp1").material("mat3").set("fresnel", 0.99);
    model.component("comp1").material("mat3").set("roughness", 0.02);
    model.component("comp1").material("mat3").set("shininess", 200);
    model.component("comp1").material("mat3").set("alpha", 1);

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(3);

    model.component("comp1").material("mat3").selection().set(6);
    model.component("comp1").material("mat3").propertyGroup("def").set("relpermittivity", new String[]{"8"});

    model.component("comp1").physics("es").feature().duplicate("pot5", "pot4");
    model.component("comp1").physics("es").feature("pot5").set("V0", -3000);
    model.component("comp1").physics("es").feature("pot5").selection().geom("geom1", 2);
    model.component("comp1").physics("es").feature("pot5").selection().set(21, 22, 23, 24, 67, 92);

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").feature("slc1").set("colortablesym", false);
    model.result("pg1").feature("slc1").set("colortablerev", false);
    model.result("pg3").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(3);

    model.component("comp1").physics("cpt").create("wall5", "Wall", 2);
    model.component("comp1").physics("cpt").feature("wall5").selection().set(21, 22, 23, 24, 67, 92);

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg3").run();

    model.component("comp1").physics("es").feature("pot5").active(false);
    model.component("comp1").physics("es").create("fp1", "FloatingPotential", 2);
    model.component("comp1").physics("es").feature().remove("fp1");

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();
    model.result("pg1").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.result("pg1").run();

    model.component("comp1").geom("geom1").feature("cyl11").active(false);
    model.component("comp1").geom("geom1").run();

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg3").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(91);
    model.component("comp1").view("view1").hideEntities("hide1").add(58);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);

    model.component("comp1").physics("es").feature("pot5").selection().set();

    model.component("comp1").view("view1").hideEntities().create("hide2");
    model.component("comp1").view("view1").hideEntities("hide2").geom(3);
    model.component("comp1").view("view1").hideEntities("hide2").add(1);
    model.component("comp1").view("view1").hideEntities("hide2").add(2);
    model.component("comp1").view("view1").hideEntities("hide2").add(3);

    model.result("pg3").run();

    model.component("comp1").geom("geom1").feature("cyl11").active(true);
    model.component("comp1").geom("geom1").run();

    model.component("comp1").material("mat3").selection().set(6);

    model.component("comp1").physics("es").feature("pot5").selection().set(21, 22, 23, 24, 67, 92);

    return model;
  }

  public static Model run8(Model model) {
    model.component("comp1").physics("es").feature("pot5").active(true);
    model.component("comp1").physics("cpt").feature("wall5").selection().set(21, 22, 23, 24, 67, 92);

    model.component("comp1").geom("geom1").feature("cyl11").active(false);
    model.component("comp1").geom("geom1").run();

    model.component("comp1").physics("es").feature("pot5").active(false);
    model.component("comp1").physics("cpt").feature("wall5").active(false);

    model.result("pg3").run();
    model.result("pg1").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.result("pg1").run();
    model.result("pg3").run();
    model.result("pg1").run();

    model.component("comp1").physics("es").feature("pot3").active(false);
    model.component("comp1").physics("es").feature("pot4").active(false);

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").feature("traj1").set("pointradiusexpr", "0.1");
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").feature("traj1").set("pointradiusexpr", "0.01");
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").feature("traj1").set("sphereradiusscaleactive", true);
    model.result("pg3").feature("traj1").set("sphereradiusscale", 1);
    model.result("pg3").feature("traj1").set("pointradiusexpr", "0.1");
    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("wall2").active(false);
    model.component("comp1").physics("cpt").feature("wall4").active(false);

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.label("lens8doubleMCPblank.mph");

    model.component("comp1").geom("geom1").feature("cyl11").active(true);
    model.component("comp1").geom("geom1").run("fin");

    model.component("comp1").view("view1").set("scenelight", false);
    model.component("comp1").view("view1").camera().set("projection", "perspective");
    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("fin");
    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("fin");
    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").set("renderwireframe", false);
    model.component("comp1").view("view1").set("showaxisorientation", false);
    model.component("comp1").view("view1").set("showgrid", true);
    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("fin");
    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").set("transparency", true);

    model.component("comp1").geom("geom1").feature().duplicate("cyl12", "cyl11");
    model.component("comp1").geom("geom1").feature("cyl12").label("MCP Hole 1");
    model.component("comp1").geom("geom1").feature("cyl12").set("r", 1);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("cyl12");
    model.component("comp1").geom("geom1").create("arr2", "Array");

    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4");
    model.component("comp1").view("view1").hideObjects("hide1").add("dif1");
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl11");

    model.component("comp1").geom("geom1").feature("arr2").selection("input").set("cyl12");
    model.component("comp1").geom("geom1").feature("arr2").set("displ", new int[]{2, 2, 0});
    model.component("comp1").geom("geom1").feature("arr2").set("type", "three-dimensional");
    model.component("comp1").geom("geom1").feature("arr2").set("fullsize", new int[]{5, 5, 1});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl12").set("r", 0.5);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature().duplicate("arr3", "arr2");
    model.component("comp1").geom("geom1").feature("arr3").active(false);
    model.component("comp1").geom("geom1").feature().remove("arr3");
    model.component("comp1").geom("geom1").feature("cyl12").set("pos", new int[]{-10, -10, 150});
    model.component("comp1").geom("geom1").feature("arr2").set("fullsize", new int[]{10, 10, 1});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("arr2");
    model.component("comp1").geom("geom1").create("dif6", "Difference");

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4");
    model.component("comp1").view("view1").hideObjects("hide1").add("dif1");

    model.component("comp1").geom("geom1").feature("dif6").selection("input").set("cyl11");
    model.component("comp1").geom("geom1").feature("dif6").selection("input2").set("arr2(10,2,1)");
    model.component("comp1").geom("geom1").feature("dif6").selection("input2").init();
    model.component("comp1").geom("geom1").feature("arr2").set("selresult", true);
    model.component("comp1").geom("geom1").run("arr2");
    model.component("comp1").geom("geom1").feature("dif6").selection("input2").named("arr2");
    model.component("comp1").geom("geom1").feature("dif6").set("selresult", true);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();
    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(3);

    model.component("comp1").material("mat3").selection().set(6);
    model.component("comp1").material("mat1").selection().set(1, 2, 3, 4, 5, 7, 8);

    model.component("comp1").physics("es").feature("pot3").active(true);
    model.component("comp1").physics("es").feature("pot4").active(true);
    model.component("comp1").physics("es").feature("pot5").selection().set(24);
    model.component("comp1").physics("es").feature("pot5").active(true);
    model.component("comp1").physics("es").feature().duplicate("pot6", "pot5");
    model.component("comp1").physics("es").feature("pot6").set("V0", -200);
    model.component("comp1").physics("es").feature("pot6").selection().set(23);
    model.component("comp1").physics("cpt").feature("wall2").active(true);
    model.component("comp1").physics("cpt").feature("wall4").active(true);

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();
    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(337);
    model.component("comp1").view("view1").hideEntities("hide1").add(282);
    model.component("comp1").view("view1").hideEntities("hide1").add(4);
    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4");
    model.component("comp1").view("view1").hideObjects("hide1").add("dif1");
    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();
    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(5);
    model.component("comp1").view("view1").hideEntities("hide1").add(9);
    model.component("comp1").view("view1").hideEntities("hide1").add(335);
    model.component("comp1").view("view1").hideEntities("hide1").add(336);
    model.component("comp1").view("view1").hideEntities("hide1").add(337);

    model.component("comp1").physics("cpt").feature("wall5").selection().set(23, 24);
    model.component("comp1").physics("cpt").feature("wall5").active(true);

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.component("comp1").geom("geom1").feature("cyl11").set("h", 0.5);
    model.component("comp1").geom("geom1").feature("cyl12").set("h", 0.5);
    model.component("comp1").geom("geom1").run("fin");

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.component("comp1").mesh("mesh1").autoMeshSize(1);
    model.component("comp1").mesh("mesh1").run();

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.component("comp1").geom("geom1").feature().duplicate("cyl13", "cyl11");
    model.component("comp1").geom("geom1").feature("cyl13").set("pos", new double[]{0, 0, 150.5});
    model.component("comp1").geom("geom1").feature("cyl13").label("MCP Back 1");
    model.component("comp1").geom("geom1").run();

    model.component("comp1").view("view1").set("scenelight", false);
    model.component("comp1").view("view1").hideEntities().create("hide2");
    model.component("comp1").view("view1").hideEntities("hide2").geom(3);
    model.component("comp1").view("view1").hideEntities("hide2").add(1);
    model.component("comp1").view("view1").hideEntities("hide2").add(2);
    model.component("comp1").view("view1").hideEntities("hide2").add(3);

    model.component("comp1").material("mat3").selection().set(6, 7);
    model.component("comp1").material("mat1").selection().set(1, 2, 3, 4, 5, 8, 9);

    model.component("comp1").physics("es").feature("pot5").selection().set(26, 27);
    model.component("comp1").physics("cpt").feature("wall5").selection().set(23, 26, 27);

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 985, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 558, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 272, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 258, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 148, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 80, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 94, 0);
    model.result("pg3").run();

    model.component("comp1").view("view1").camera().set("projection", "orthographic");

    model.result("pg1").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").set("showlegendsmaxmin", false);
    model.result("pg1").run();
    model.result("pg1").feature("slc1").set("rangecoloractive", true);
    model.result("pg1").feature("slc1").set("rangecolormin", -500);
    model.result("pg1").feature("slc1").set("rangecolormax", 10);
    model.result("pg1").feature("slc1").set("rangecolormin", -300);
    model.result("pg1").run();
    model.result("pg3").run();

    model.component("comp1").physics("es").feature("pot6").set("V0", 0);
    model.component("comp1").physics("es").feature("pot6").active(false);

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(345);
    model.component("comp1").view("view1").hideEntities("hide1").add(346);
    model.component("comp1").view("view1").hideEntities("hide1").add(347);
    model.component("comp1").view("view1").hideEntities("hide1").add(9);
    model.component("comp1").view("view1").hideEntities("hide1").add(402);
    model.component("comp1").view("view1").hideEntities("hide1").add(5);
    model.component("comp1").view("view1").hideEntities("hide1").add(401);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(400);
    model.component("comp1").view("view1").hideEntities("hide1").add(10);
    model.component("comp1").view("view1").hideEntities("hide1").add(6);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);

    model.label("lens8doubleMCPhole2.mph");

    model.result("pg1").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 6, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 34, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 66, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 104, 0);
    model.result("pg3").run();
    model.result("pg1").run();
    model.result("pg1").run();

    model.component("comp1").geom("geom1").run("cyl13");
    model.component("comp1").geom("geom1").create("imp1", "Import");

    model.sol("sol1").clearSolutionData();
    model.sol("sol2").clearSolutionData();

    model.component("comp1").geom("geom1").run("cyl13");
    model.component("comp1").geom("geom1").run("cyl13");
    model.component("comp1").geom("geom1").create("imp2", "Import");
    model.component("comp1").geom("geom1").feature("imp2")
         .set("filename", "C:\\Users\\dvin\\Downloads\\chamber_take10.step");
    model.component("comp1").geom("geom1").feature("imp2").set("selresult", true);
    model.component("comp1").geom("geom1").run("imp2");
    model.component("comp1").geom("geom1").feature("cyl4").set("h", 400);
    model.component("comp1").geom("geom1").feature("cyl4").set("pos", new int[]{0, 0, -100});
    model.component("comp1").geom("geom1").feature("cyl4").set("r", 150);
    model.component("comp1").geom("geom1").run("cyl4");
    model.component("comp1").geom("geom1").feature("cyl4").set("pos", new int[]{0, 0, -50});
    model.component("comp1").geom("geom1").run("cyl4");
    model.component("comp1").geom("geom1").run("imp2");
    model.component("comp1").geom("geom1").feature().remove("imp1");
    model.component("comp1").geom("geom1").run("fin");

    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("fin");
    model.component("comp1").view("view1").hideObjects().clear();

    model.component("comp1").geom("geom1").feature().move("imp2", 0);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature().move("cyl4", 0);
    model.component("comp1").geom("geom1").runPre("fin");

    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4");

    model.label("lens8doubleMCPhole2tcad.mph");

    model.component("comp1").geom("geom1").run("cyl13");
    model.component("comp1").geom("geom1").create("imp3", "Import");
    model.component("comp1").geom("geom1").feature("imp3").set("filename", "D:\\CAD\\rod_11.step");
    model.component("comp1").geom("geom1").feature("imp3").set("selresult", true);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("imp3");
    model.component("comp1").geom("geom1").create("imp4", "Import");
    model.component("comp1").geom("geom1").feature("imp4").set("filename", "D:\\CAD\\IFE_Setup_LMcombo.step");
    model.component("comp1").geom("geom1").run("imp3");

    model.label("lens8doubleMCPhole2tcad.mph");

    model.component("comp1").geom("geom1").feature("imp4").set("filename", "D:\\CAD\\IFE_Setup_LM_ground.step");
    model.component("comp1").geom("geom1").run("imp4");
    model.component("comp1").geom("geom1").feature("imp3").active(false);
    model.component("comp1").geom("geom1").feature("imp2").active(false);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("imp4");
    model.component("comp1").geom("geom1").create("rot1", "Rotate");
    model.component("comp1").geom("geom1").feature("rot1").selection("input").set("imp4.Body1(1)");
    model.component("comp1").geom("geom1").feature("rot1").set("axistype", "y");
    model.component("comp1").geom("geom1").feature("rot1").set("rot", 90);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").runPre("rot1");
    model.component("comp1").geom("geom1").feature("rot1").set("selresult", true);
    model.component("comp1").geom("geom1").feature("imp4").set("selresult", true);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("rot1").active(false);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("imp4").set("selindividual", true);
    model.component("comp1").geom("geom1").selection().create("csel1", "CumulativeSelection");
    model.component("comp1").geom("geom1").selection("csel1").label("Cumulative Selection 1");
    model.component("comp1").geom("geom1").feature("imp4").set("contributeto", "csel1");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").runPre("rot1");
    model.component("comp1").geom("geom1").feature("rot1").selection("input").named("csel1");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("rot1").active(true);
    model.component("comp1").geom("geom1").runPre("fin");

    return model;
  }

  public static Model run9(Model model) {
    model.component("comp1").geom("geom1").run("rot1");
    model.component("comp1").geom("geom1").create("mov1", "Move");
    model.component("comp1").geom("geom1").feature("mov1").selection("input").named("rot1");
    model.component("comp1").geom("geom1").feature("mov1").set("displz", -600);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl1").active(false);
    model.component("comp1").geom("geom1").run("cyl3");
    model.component("comp1").geom("geom1").feature("cyl3").active(false);
    model.component("comp1").geom("geom1").feature("dif1").active(false);
    model.component("comp1").geom("geom1").runPre("fin");

    model.component("comp1").view("view1").set("showgrid", true);

    model.component("comp1").geom("geom1").feature("cyl2").set("pos", new int[]{0, 0, 60});
    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").feature("cyl2").set("pos", new int[]{0, 0, 50});
    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").run("mov1");
    model.component("comp1").geom("geom1").create("mov2", "Move");
    model.component("comp1").geom("geom1").feature("mov2").selection("input").set("cone1", "copy1", "cyl2", "uni1");
    model.component("comp1").geom("geom1").feature("mov2").set("displz", 50);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("mov2").set("displz", 15);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").runPre("mov2");
    model.component("comp1").geom("geom1").feature("mov2").selection("input")
         .set("cone1", "copy1", "cyl13", "cyl2", "dif6", "uni1");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.component("comp1").geom("geom1").feature("cyl4").set("r", 175);
    model.component("comp1").geom("geom1").run("fin");

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);

    model.component("comp1").physics("es").feature("pot6").active(true);
    model.component("comp1").physics("es").feature("pot6").set("V0", -50);

    model.component("comp1").mesh("mesh1").autoMeshSize(2);
    model.component("comp1").mesh("mesh1").run();
    model.component("comp1").mesh("mesh1").automatic(false);
    model.component("comp1").mesh("mesh1").create("size1", "Size");
    model.component("comp1").mesh("mesh1").feature("size1").selection().geom("geom1", 3);
    model.component("comp1").mesh("mesh1").feature("size1").selection().set(2);
    model.component("comp1").mesh("mesh1").run("size1");
    model.component("comp1").mesh("mesh1").feature().move("size1", 1);
    model.component("comp1").mesh("mesh1").run("size1");
    model.component("comp1").mesh("mesh1").run("size1");
    model.component("comp1").mesh("mesh1").feature("size").set("hauto", 4);
    model.component("comp1").mesh("mesh1").create("size2", "Size");
    model.component("comp1").mesh("mesh1").feature("size2").selection().geom("geom1", 3);
    model.component("comp1").mesh("mesh1").feature("size2").selection().all();
    model.component("comp1").mesh("mesh1").feature("size2").selection()
         .set(3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26);
    model.component("comp1").mesh("mesh1").feature("size2").set("hauto", 4);

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.component("comp1").mesh("mesh1").feature("size1").selection().set(1, 2);

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);

    model.component("comp1").mesh("mesh1").current("ftet1");

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.component("comp1").mesh("mesh1").create("ftet2", "FreeTet");
    model.component("comp1").mesh("mesh1").feature("size").set("custom", false);
    model.component("comp1").mesh("mesh1").feature("size").set("hauto", 5);
    model.component("comp1").mesh("mesh1").feature("ftet1").active(false);
    model.component("comp1").mesh("mesh1").feature("ftet2").active(false);
    model.component("comp1").mesh("mesh1").run();
    model.component("comp1").mesh("mesh1").create("ftet3", "FreeTet");
    model.component("comp1").mesh("mesh1").feature("ftet3").create("size1", "Size");
    model.component("comp1").mesh("mesh1").feature("size1").active(false);
    model.component("comp1").mesh("mesh1").feature("size2").active(false);
    model.component("comp1").mesh("mesh1").feature("ftet3").selection().geom("geom1", 3);
    model.component("comp1").mesh("mesh1").feature("ftet3").selection().named("geom1_imp4_Body1_5_dom");
    model.component("comp1").mesh("mesh1").feature("ftet3").selection().all();
    model.component("comp1").mesh("mesh1").feature("ftet3").selection().set(1, 2);
    model.component("comp1").mesh("mesh1").create("ftet4", "FreeTet");
    model.component("comp1").mesh("mesh1").feature("ftet4").create("size1", "Size");
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size1").set("hauto", 3);
    model.component("comp1").mesh("mesh1").feature("ftet3").feature("size1").set("hauto", 3);
    model.component("comp1").mesh("mesh1").feature().duplicate("ftet5", "ftet3");
    model.component("comp1").mesh("mesh1").feature().move("ftet5", 3);
    model.component("comp1").mesh("mesh1").feature("ftet5").selection().set(1);
    model.component("comp1").mesh("mesh1").feature("ftet5").feature("size1").set("hauto", 6);
    model.component("comp1").mesh("mesh1").feature("ftet3").feature("size1").selection().set(2);
    model.component("comp1").mesh("mesh1").current("ftet4");

    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("fin");
    model.component("comp1").view("view1").hideObjects().clear();

    model.component("comp1").mesh("mesh1").feature("ftet3").selection().set(2);
    model.component("comp1").mesh("mesh1").feature("ftet3").feature("size1").set("hauto", 2);

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(551);
    model.component("comp1").view("view1").hideEntities("hide1").add(604);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);

    model.component("comp1").mesh("mesh1").feature("ftet5").selection().geom("geom1");
    model.component("comp1").mesh("mesh1").feature("ftet5").selection().geom("geom1", 3);
    model.component("comp1").mesh("mesh1").feature("ftet5").selection().set(1);
    model.component("comp1").mesh("mesh1").feature("ftet5").feature("size1").selection().geom("geom1", 2);
    model.component("comp1").mesh("mesh1").feature("ftet5").feature("size1").selection().set(1, 3, 4);

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.component("comp1").mesh("mesh1").feature("ftet5").feature("size1").selection().set(1, 2, 3, 4, 551, 604);
    model.component("comp1").mesh("mesh1").feature().move("ftet3", 3);
    model.component("comp1").mesh("mesh1").feature("ftet3").feature("size1").set("hauto", 3);
    model.component("comp1").mesh("mesh1").run();
    model.component("comp1").mesh("mesh1").feature("ftet3").feature("size1").set("hauto", 4);
    model.component("comp1").mesh("mesh1").run();

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");

    model.component("comp1").material("mat1").selection().all();

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg1").run();

    model.component("comp1").geom("geom1").feature().duplicate("cyl14", "cyl13");
    model.component("comp1").geom("geom1").feature("cyl14").label("MCP Holder");
    model.component("comp1").geom("geom1").feature("cyl14").set("h", 8);
    model.component("comp1").geom("geom1").feature("cyl14").set("pos", new int[]{0, 0, 151});
    model.component("comp1").geom("geom1").feature("cyl14").set("r", 40);
    model.component("comp1").geom("geom1").runPre("fin");

    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4");
    model.component("comp1").view("view1").hideObjects("hide1").add("mov1(1)");

    model.component("comp1").geom("geom1").feature().move("cyl14", 30);
    model.component("comp1").geom("geom1").runPre("mov2");
    model.component("comp1").geom("geom1").feature("mov2").selection("input")
         .set("cone1", "copy1", "cyl13", "cyl14", "cyl2", "dif6", "uni1");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run();

    model.component("comp1").material().create("mat4", "Common");
    model.component("comp1").material("mat4").propertyGroup().create("Enu", "Young's modulus and Poisson's ratio");
    model.component("comp1").material("mat4").label("Polyimide");
    model.component("comp1").material("mat4").set("groups", new String[][]{{"polymers", "Polymers"}});
    model.component("comp1").material("mat4").propertyGroup("def").set("heatcapacity", "1100[J/(kg*K)]");
    model.component("comp1").material("mat4").propertyGroup("def").descr("heatcapacity_symmetry", "");
    model.component("comp1").material("mat4").propertyGroup("def").set("density", "1300[kg/m^3]");
    model.component("comp1").material("mat4").propertyGroup("def").descr("density_symmetry", "");
    model.component("comp1").material("mat4").propertyGroup("def")
         .set("thermalconductivity", new String[]{"0.15[W/(m*K)]", "0", "0", "0", "0.15[W/(m*K)]", "0", "0", "0", "0.15[W/(m*K)]"});
    model.component("comp1").material("mat4").propertyGroup("def").descr("thermalconductivity_symmetry", "");
    model.component("comp1").material("mat4").propertyGroup("Enu").set("youngsmodulus", "3.1e9[Pa]");
    model.component("comp1").material("mat4").propertyGroup("Enu").descr("youngsmodulus_symmetry", "");
    model.component("comp1").material("mat4").propertyGroup("Enu").descr("poissonsratio_symmetry", "");
    model.component("comp1").material("mat4").set("groups", new String[][]{});
    model.component("comp1").material("mat4").set("family", "plastic");
    model.component("comp1").material().create("mat5", "Common");
    model.component("comp1").material("mat5").propertyGroup().create("DielectricLoss", "Dielectric losses");
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").func().create("int1", "Interpolation");
    model.component("comp1").material("mat5").propertyGroup()
         .create("LossTangentDF", "Loss tangent, dissipation factor");
    model.component("comp1").material("mat5").propertyGroup("LossTangentDF").func().create("int1", "Interpolation");
    model.component("comp1").material("mat5").label("P25N Polyimide-based No Flow Prepreg");
    model.component("comp1").material("mat5").set("groups", new String[][]{{"Isola", "Isola Group"}});
    model.component("comp1").material("mat5").propertyGroup("def")
         .set("relpermeability", new String[]{"1", "0", "0", "0", "1", "0", "0", "0", "1"});
    model.component("comp1").material("mat5").propertyGroup("def").descr("relpermeability_symmetry", "");
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").func("int1")
         .set("funcname", "epsilonPrim_iso_interp");
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").func("int1")
         .set("table", new String[][]{{"100e6", "3.75"}, {"500e6", "3.72"}, {"1e9", "3.70"}, {"2e9", "3.67"}});
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").func("int1").set("extrap", "linear");
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").set("epsilonBis", "");
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").set("epsilonPrim", "");
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").set("eta_epsilon", "");
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").set("epsilonBis", "");
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").set("epsilonPrim", "");
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").set("eta_epsilon", "");
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").set("epsilonBis", "");
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").set("epsilonPrim", "");
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").set("eta_epsilon", "");
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").set("epsilonBis", "");
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").set("epsilonPrim", "");
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").set("eta_epsilon", "");
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").set("epsilonBis", "");
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").set("epsilonPrim", "");
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").set("eta_epsilon", "");
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").set("epsilonBis", "");
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").set("epsilonPrim", "");
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").set("eta_epsilon", "");
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").set("epsilonBis", "");
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").set("epsilonPrim", "");
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").set("eta_epsilon", "");
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss")
         .set("epsilonPrim", new String[]{"epsilonPrim_iso_interp(freq/1[Hz])", "0", "0", "0", "epsilonPrim_iso_interp(freq/1[Hz])", "0", "0", "0", "epsilonPrim_iso_interp(freq/1[Hz])"});
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss")
         .set("eta_epsilon", new String[]{"0", "0", "0", "0", "0", "0", "0", "0", "0"});
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").descr("epsilonBis_symmetry", "");
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").descr("epsilonPrim_symmetry", "");
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").descr("eta_epsilon_symmetry", "");
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss").addInput("frequency");
    model.component("comp1").material("mat5").propertyGroup("LossTangentDF").func("int1")
         .set("funcname", "tanDelta_interp");
    model.component("comp1").material("mat5").propertyGroup("LossTangentDF").func("int1")
         .set("table", new String[][]{{"100e6", "0.0140"}, {"500e6", "0.0157"}, {"1e9", "0.0180"}, {"2e9", "0.0198"}});
    model.component("comp1").material("mat5").propertyGroup("LossTangentDF").func("int1").set("extrap", "linear");
    model.component("comp1").material("mat5").propertyGroup("LossTangentDF").set("tanDelta", "");
    model.component("comp1").material("mat5").propertyGroup("LossTangentDF").set("epsilonPrim", "");
    model.component("comp1").material("mat5").propertyGroup("LossTangentDF").set("tanDelta", "");
    model.component("comp1").material("mat5").propertyGroup("LossTangentDF").set("epsilonPrim", "");
    model.component("comp1").material("mat5").propertyGroup("LossTangentDF").set("tanDelta", "");
    model.component("comp1").material("mat5").propertyGroup("LossTangentDF").set("epsilonPrim", "");
    model.component("comp1").material("mat5").propertyGroup("LossTangentDF").set("tanDelta", "");
    model.component("comp1").material("mat5").propertyGroup("LossTangentDF").set("epsilonPrim", "");
    model.component("comp1").material("mat5").propertyGroup("LossTangentDF").set("tanDelta", "");
    model.component("comp1").material("mat5").propertyGroup("LossTangentDF").set("epsilonPrim", "");
    model.component("comp1").material("mat5").propertyGroup("LossTangentDF").set("tanDelta", "");
    model.component("comp1").material("mat5").propertyGroup("LossTangentDF").set("epsilonPrim", "");
    model.component("comp1").material("mat5").propertyGroup("LossTangentDF").set("tanDelta", "");
    model.component("comp1").material("mat5").propertyGroup("LossTangentDF").set("epsilonPrim", "");
    model.component("comp1").material("mat5").propertyGroup("LossTangentDF")
         .set("tanDelta", "tanDelta_interp(freq/1[Hz])");
    model.component("comp1").material("mat5").propertyGroup("LossTangentDF").descr("tanDelta_symmetry", "");
    model.component("comp1").material("mat5").propertyGroup("LossTangentDF").descr("epsilonPrim_symmetry", "");
    model.component("comp1").material("mat5").propertyGroup("LossTangentDF").addInput("frequency");
    model.component("comp1").material("mat5").set("groups", new String[][]{});
    model.component("comp1").material("mat5").set("family", "plastic");
    model.component("comp1").material().create("mat6", "Common");
    model.component("comp1").material("mat6").label("Kapton H (Polyimide tape) [solid]");
    model.component("comp1").material("mat6").propertyGroup("def").set("thermalconductivity", "k(T[1/K])[W/(m*K)]");
    model.component("comp1").material("mat6").propertyGroup("def").set("heatcapacity", "C(T[1/K])[J/(kg*K)]");
    model.component("comp1").material("mat6").propertyGroup("def").func().create("k", "Piecewise");
    model.component("comp1").material("mat6").propertyGroup("def").func("k").set("funcname", "k");
    model.component("comp1").material("mat6").propertyGroup("def").func("k").set("arg", "T");
    model.component("comp1").material("mat6").propertyGroup("def").func("k").set("extrap", "constant");
    model.component("comp1").material("mat6").propertyGroup("def").func("k")
         .set("pieces", new String[][]{{"5.0", "400.0", "-1.82146E-15+0.0027*T^1"}});
    model.component("comp1").material("mat6").propertyGroup("def").func("k").label("Piecewise");
    model.component("comp1").material("mat6").propertyGroup("def").func("k").set("fununit", "");
    model.component("comp1").material("mat6").propertyGroup("def").func("k").set("argunit", "");
    model.component("comp1").material("mat6").propertyGroup("def").func().create("C", "Piecewise");
    model.component("comp1").material("mat6").propertyGroup("def").func("C").set("funcname", "C");
    model.component("comp1").material("mat6").propertyGroup("def").func("C").set("arg", "T");
    model.component("comp1").material("mat6").propertyGroup("def").func("C").set("extrap", "constant");
    model.component("comp1").material("mat6").propertyGroup("def").func("C")
         .set("pieces", new String[][]{{"4.0", "30.0", "2.80966562-1.39434854*T^1+0.210663856*T^2+0.00475201566*T^3-3.27999785E-4*T^4+4.28224869E-6*T^5"}, {"30.0", "300.0", "-86.8694632+7.81691699*T^1-0.0366478819*T^2+9.91279974E-5*T^3-1.08440954E-7*T^4"}});
    model.component("comp1").material("mat6").propertyGroup("def").func("C").label("Piecewise 1");
    model.component("comp1").material("mat6").propertyGroup("def").func("C").set("fununit", "");
    model.component("comp1").material("mat6").propertyGroup("def").func("C").set("argunit", "");
    model.component("comp1").material("mat6").propertyGroup("def").addInput("temperature");
    model.component("comp1").material("mat6").active(false);
    model.component("comp1").material("mat5").active(false);
    model.component("comp1").material("mat5").propertyGroup("LossTangentDF").set("epsilonPrim", new String[]{"3"});
    model.component("comp1").material("mat5").propertyGroup("DielectricLoss")
         .set("epsilonBis", new String[]{"0.05"});
    model.component("comp1").material("mat5").active(true);
    model.component("comp1").material("mat4").active(false);

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();
    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);

    model.component("comp1").material("mat4").selection().set();
    model.component("comp1").material("mat5").selection().set(13);
    model.component("comp1").material("mat5").propertyGroup("def").set("relpermittivity", new String[]{"3"});

    model.component("comp1").mesh("mesh1").run();

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.result("pg1").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 115, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 134, 0);
    model.result("pg3").run();
    model.result("pg1").run();
    model.result("pg3").run();

    model.component("comp1").view("view1").set("transparency", true);
    model.component("comp1").view("view1").camera().set("projection", "orthographic");

    model.result("pg3").set("showhiddenobjects", true);
    model.result("pg3").run();
    model.result("pg3").set("showhiddenobjects", false);
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").run();

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(555);
    model.component("comp1").view("view1").hideEntities("hide1").add(610);
    model.component("comp1").view("view1").hideEntities("hide1").add(4);

    model.result("pg3").run();

    model.component("comp1").geom("geom1").run("mov2");
    model.component("comp1").geom("geom1").create("blk1", "Block");
    model.component("comp1").geom("geom1").feature().remove("blk1");
    model.component("comp1").geom("geom1").feature().duplicate("cyl15", "cyl11");
    model.component("comp1").geom("geom1").feature("cyl15").label("MCP Shutter");
    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").feature("cyl15").set("pos", new int[]{0, 40, 150});
    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").feature("cyl15").set("pos", new int[]{40, 0, 150});
    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").feature("cyl15").set("h", 1);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run();

    model.component("comp1").mesh("mesh1").run();

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);

    return model;
  }

  public static Model run10(Model model) {
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").feature().duplicate("slc2", "slc1");
    model.result("pg1").run();
    model.result("pg1").feature("slc2").set("quickplane", "zx");
    model.result("pg1").run();
    model.result("pg1").feature("slc2").set("quickynumber", 1);
    model.result("pg1").run();
    model.result("pg3").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.label("lens8doubleMCPhole4tcadshutter.mph");

    model.result("pg3").run();
    model.result("pg1").run();
    model.result("pg3").run();
    model.result("pg1").run();

    model.label("lens8doubleMCPhole4tcadshutter.mph");

    model.result("pg1").run();

    model.component("comp1").geom("geom1").run("cyl15");
    model.component("comp1").geom("geom1").create("imp5", "Import");
    model.component("comp1").geom("geom1").feature("imp5")
         .set("filename", "C:\\Users\\dvin\\Downloads\\mcp holder v2 STP.STEP");
    model.component("comp1").geom("geom1").feature("imp5").set("selresult", true);
    model.component("comp1").geom("geom1").feature("imp5").set("selresultshow", "dom");
    model.component("comp1").geom("geom1").run("imp5");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("imp5");
    model.component("comp1").geom("geom1").create("mov3", "Move");
    model.component("comp1").geom("geom1").feature("mov3").selection("input").named("imp5");
    model.component("comp1").geom("geom1").feature("mov3").set("displx", 200);
    model.component("comp1").geom("geom1").run("mov3");
    model.component("comp1").geom("geom1").feature("mov3").set("displx", 0);
    model.component("comp1").geom("geom1").feature("mov3").set("displz", 200);
    model.component("comp1").geom("geom1").run("mov3");
    model.component("comp1").geom("geom1").feature("mov3").set("displz", 180);
    model.component("comp1").geom("geom1").run("mov3");
    model.component("comp1").geom("geom1").feature("mov3").set("displz", 165);
    model.component("comp1").geom("geom1").run("mov3");
    model.component("comp1").geom("geom1").feature("cyl13").active(false);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl14").active(false);
    model.component("comp1").geom("geom1").runPre("fin");

    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4");
    model.component("comp1").view("view1").hideObjects("hide1").add("mov1(1)");

    model.component("comp1").geom("geom1").feature("cyl15").active(false);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("mov3");
    model.component("comp1").geom("geom1").create("cyl16", "Cylinder");
    model.component("comp1").geom("geom1").feature("cyl16").set("h", 3);
    model.component("comp1").geom("geom1").feature("cyl16").set("r", 37.5);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl16").set("pos", new int[]{0, 0, 180});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl16").set("pos", new int[]{0, 0, 200});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature().duplicate("cyl17", "cyl16");
    model.component("comp1").geom("geom1").feature("cyl17").set("h", 8.9);
    model.component("comp1").geom("geom1").feature("cyl17").set("r", 27.5);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl17").set("pos", new String[]{"0", "0", "200-8.9-3"});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl17").set("pos", new String[]{"0", "0", "200-8.9"});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature().duplicate("cyl18", "cyl17");
    model.component("comp1").geom("geom1").feature("cyl18").set("h", 3.3);
    model.component("comp1").geom("geom1").feature("cyl18").set("r", 16);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("cyl18");
    model.component("comp1").geom("geom1").create("uni2", "Union");
    model.component("comp1").geom("geom1").feature("uni2").selection("input").set("cyl16", "cyl17");
    model.component("comp1").geom("geom1").run("uni2");
    model.component("comp1").geom("geom1").run("uni2");
    model.component("comp1").geom("geom1").create("dif7", "Difference");
    model.component("comp1").geom("geom1").feature("dif7").selection("input2").set("cyl18");
    model.component("comp1").geom("geom1").run("uni2");
    model.component("comp1").geom("geom1").feature("dif7").selection("input").set("uni2");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("dif7");
    model.component("comp1").geom("geom1").create("mov4", "Move");
    model.component("comp1").geom("geom1").feature("mov4").selection("input").init();
    model.component("comp1").geom("geom1").feature("mov4").selection("input").set("dif7");
    model.component("comp1").geom("geom1").feature("mov4").set("displz", -30);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("mov4").set("displz", -25);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("mov3").set("displz", 185);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("mov3").set("displz", 175);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("mov3").set("displz", 180);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("mov3").set("displz", 18078);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("mov3").set("displz", 1878);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("mov3").set("displz", 178);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("mov3").set("displz", 278);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("mov4").set("displz", -125);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("mov4").set("displz", 75);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl11").active(false);
    model.component("comp1").geom("geom1").feature("cyl12").active(false);
    model.component("comp1").geom("geom1").feature("arr2").active(false);
    model.component("comp1").geom("geom1").feature("dif6").active(false);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();
    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);

    model.component("comp1").material("mat3").selection().set(14, 17);
    model.component("comp1").material("mat5").selection().set(3);

    model.component("comp1").physics("es").feature("pot3").set("V0", -120);
    model.component("comp1").physics("es").feature("pot4").set("V0", 60);
    model.component("comp1").physics("es").feature("pot5").selection().set(236);
    model.component("comp1").physics("es").feature("pot5").set("V0", -10000);
    model.component("comp1").physics("es").feature("pot6").selection().set(229);
    model.component("comp1").physics("es").feature("pot6").set("V0", -12000);

    model.component("comp1").mesh("mesh1").feature().remove("ftet1");
    model.component("comp1").mesh("mesh1").feature().remove("ftet2");
    model.component("comp1").mesh("mesh1").feature().remove("size1");
    model.component("comp1").mesh("mesh1").feature().remove("size2");

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();
    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(4);
    model.component("comp1").view("view1").hideEntities("hide1").add(298);
    model.component("comp1").view("view1").hideEntities("hide1").add(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(333);

    model.component("comp1").mesh("mesh1").feature("ftet5").feature("size1").selection().geom("geom1", 3);
    model.component("comp1").mesh("mesh1").feature("ftet5").feature("size1").selection().geom("geom1", 2);

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.component("comp1").mesh("mesh1").feature("ftet5").feature("size1").selection().set(3);
    model.component("comp1").mesh("mesh1").feature().move("ftet5", 1);
    model.component("comp1").mesh("mesh1").feature("ftet5").feature("size1").selection().geom("geom1", 3);
    model.component("comp1").mesh("mesh1").feature("ftet5").feature("size1").selection().set(1);

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);

    model.component("comp1").mesh("mesh1").feature("ftet4").selection().geom("geom1", 3);
    model.component("comp1").mesh("mesh1").feature("ftet4").selection().all();
    model.component("comp1").mesh("mesh1").feature("ftet4").selection()
         .set(3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27);
    model.component("comp1").mesh("mesh1").feature().move("ftet4", 1);

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();
    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);

    model.component("comp1").mesh("mesh1").feature("ftet5").feature("size1").selection().named("geom1_imp2_dom");
    model.component("comp1").mesh("mesh1").feature("ftet5").feature("size1").selection().named("geom1_csel1_dom");
    model.component("comp1").mesh("mesh1").feature("ftet5").feature("size1").selection().named("geom1_imp2_dom");
    model.component("comp1").mesh("mesh1").feature("ftet5").feature("size1").selection()
         .named("geom1_imp4_Body1_1_dom");
    model.component("comp1").mesh("mesh1").feature("ftet5").feature("size1").selection()
         .named("geom1_imp4_Body1_2_dom");
    model.component("comp1").mesh("mesh1").feature("ftet5").feature("size1").selection()
         .named("geom1_imp4_Body1_1_dom");
    model.component("comp1").mesh("mesh1").feature("ftet5").selection().named("geom1_imp4_Body1_1_dom");
    model.component("comp1").mesh("mesh1").feature("ftet5").feature("size1").set("hauto", 4);
    model.component("comp1").mesh("mesh1").feature("ftet3").selection().remaining();
    model.component("comp1").mesh("mesh1").feature("ftet3").feature("size1").set("hauto", 6);
    model.component("comp1").mesh("mesh1").current("ftet3");
    model.component("comp1").mesh("mesh1").feature("ftet3").feature("size1").set("hauto", 5);
    model.component("comp1").mesh("mesh1").feature("ftet3").feature("size1").selection().geom("geom1", 2);

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.component("comp1").mesh("mesh1").feature("ftet3").feature("size1").selection().set(1, 2, 3, 4, 298, 333);
    model.component("comp1").mesh("mesh1").feature().duplicate("ftet6", "ftet5");
    model.component("comp1").mesh("mesh1").feature().move("ftet6", 3);
    model.component("comp1").mesh("mesh1").feature("ftet6").selection().all();
    model.component("comp1").mesh("mesh1").feature("ftet6").selection().set(1);

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.sol("sol1").clearSolutionData();
    model.sol("sol2").clearSolutionData();

    model.component("comp1").mesh("mesh1").feature("ftet4").selection().geom("geom1");
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size1").selection().geom("geom1", 3);
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size1").selection().all();
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size1").selection()
         .set(3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27);
    model.component("comp1").mesh("mesh1").feature("ftet4").create("size2", "Size");
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size2").selection().geom("geom1", 3);
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size2").selection().all();
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size2").selection().set(2);
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size2").set("hauto", 4);
    model.component("comp1").mesh("mesh1").feature("ftet4").create("size3", "Size");
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size3").selection().geom("geom1", 3);
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size3").selection().all();
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size3").selection().set(1);

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);

    model.component("comp1").mesh("mesh1").feature("ftet5").active(false);
    model.component("comp1").mesh("mesh1").feature("ftet6").active(false);
    model.component("comp1").mesh("mesh1").feature("ftet3").active(false);
    model.component("comp1").mesh("mesh1").current("ftet4");
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size3").selection().geom("geom1", 2);

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size3").selection().set(1, 2, 3, 4, 298, 333);

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(333);
    model.component("comp1").view("view1").hideEntities("hide1").add(4);
    model.component("comp1").view("view1").hideEntities("hide1").add(28);
    model.component("comp1").view("view1").hideEntities("hide1").add(42);
    model.component("comp1").view("view1").hideEntities("hide1").add(27);
    model.component("comp1").view("view1").hideEntities("hide1").add(25);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(298);
    model.component("comp1").view("view1").hideEntities("hide1").add(26);
    model.component("comp1").view("view1").hideEntities("hide1").add(48);
    model.component("comp1").view("view1").hideEntities("hide1").add(40);
    model.component("comp1").view("view1").hideEntities("hide1").add(47);
    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.component("comp1").geom("geom1").feature("mov4").set("displz", 50);
    model.component("comp1").geom("geom1").feature("mov3").set("displz", 253);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("mov4");
    model.component("comp1").geom("geom1").create("cyl19", "Cylinder");
    model.component("comp1").geom("geom1").feature("cyl19").set("r", 4);
    model.component("comp1").geom("geom1").feature("cyl19").set("h", 10);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl19").set("pos", new int[]{0, 0, 180});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl19").set("pos", new int[]{0, 0, 260});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl19").set("pos", new int[]{0, 0, 250});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl19").set("h", 20);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl19").set("pos", new int[]{0, 0, 245});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl19").set("pos", new double[]{44.45, 44.45, 245});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl19").set("r", 5);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("cyl19");
    model.component("comp1").geom("geom1").create("arr3", "Array");
    model.component("comp1").geom("geom1").feature("arr3").selection("input").set("cyl4");
    model.component("comp1").geom("geom1").feature("arr3").selection("input").init();
    model.component("comp1").geom("geom1").feature("arr3").selection("input").set("cyl4");
    model.component("comp1").geom("geom1").feature("arr3").selection("input").init();

    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4");
    model.component("comp1").view("view1").hideObjects("hide1").add("mov1(1)");
    model.component("comp1").view("view1").hideObjects("hide1").add("mov3");
    model.component("comp1").view("view1").hideObjects("hide1").add("mov1(15)");

    model.component("comp1").geom("geom1").feature("arr3").selection("input").set("cyl19");
    model.component("comp1").geom("geom1").feature("arr3").set("displ", new double[]{-88.9, -88.9, 0});
    model.component("comp1").geom("geom1").feature("arr3").set("fullsize", new int[]{2, 2, 1});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("arr3");
    model.component("comp1").geom("geom1").create("dif8", "Difference");
    model.component("comp1").geom("geom1").feature("dif8").selection("input").named("imp5");
    model.component("comp1").geom("geom1").feature("dif8").selection("input2").set("arr3");
    model.component("comp1").geom("geom1").runPre("fin");

    model.component("comp1").view("view1").hideObjects().clear();

    model.component("comp1").geom("geom1").run();

    model.component("comp1").mesh("mesh1").run();

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").feature("slc1").set("rangecoloractive", false);
    model.result("pg1").run();
    model.result("pg1").feature("slc2").set("rangecoloractive", true);
    model.result("pg1").run();
    model.result("pg1").feature("slc1").set("rangecoloractive", true);
    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").feature("slc1").set("rangecolormin", -300);
    model.result("pg1").feature("slc1").set("rangecolormax", 100);
    model.result("pg1").run();
    model.result("pg1").feature("slc2").set("rangecolormax", 100);
    model.result("pg1").run();
    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("wall5").selection().all();
    model.component("comp1").physics("cpt").feature("wall3").active(false);
    model.component("comp1").physics("cpt").feature("pp1").set("mp", "1.7e-28");
    model.component("comp1").physics("cpt").feature("pbeam1").set("N", 100);

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 1001, 0);
    model.result("pg3").run();
    model.result("pg1").run();
    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("pbeam1").set("N", 1000);

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("pbeam1").set("N", 100);
    model.component("comp1").physics("es").feature("pot4").set("V0", -200);

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 38, 0);
    model.result("pg3").run();

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(23);
    model.component("comp1").view("view1").hideEntities("hide1").add(22);
    model.component("comp1").view("view1").hideEntities("hide1").add(277);
    model.component("comp1").view("view1").hideEntities("hide1").add(24);
    model.component("comp1").view("view1").hideEntities("hide1").add(275);
    model.component("comp1").view("view1").hideEntities("hide1").add(276);
    model.component("comp1").view("view1").hideEntities("hide1").add(4);
    model.component("comp1").view("view1").hideEntities("hide1").add(278);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(329);
    model.component("comp1").view("view1").hideEntities("hide1").add(294);
    model.component("comp1").view("view1").hideEntities("hide1").add(40);
    model.component("comp1").view("view1").hideEntities("hide1").add(42);
    model.component("comp1").view("view1").hideEntities("hide1").add(43);
    model.component("comp1").view("view1").hideEntities("hide1").add(41);
    model.component("comp1").view("view1").hideEntities("hide1").add(232);
    model.component("comp1").view("view1").hideEntities("hide1").add(222);
    model.component("comp1").view("view1").hideEntities("hide1").add(225);

    model.component("comp1").physics("es").feature("pot6").active(false);
    model.component("comp1").physics("es").feature("pot5").active(false);

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);

    return model;
  }

  public static Model run11(Model model) {
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("wall5").active(false);

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 6, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 2, 0);
    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("wall5").active(true);

    model.component("comp1").view("view1").hideEntities("hide1").add(2);

    model.component("comp1").physics("cpt").feature("wall5").selection()
         .set(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 288, 289, 290, 292, 293, 294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 353, 354, 355, 356, 357, 358, 359, 360, 361, 362, 363, 364, 365, 366, 367, 368, 369, 370, 371, 372, 373, 374, 375, 376, 377, 378, 379, 380, 381, 382, 383, 384, 385, 386, 387, 388, 389, 390, 391, 392, 393, 394, 395, 396, 397, 398, 399, 400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 419, 420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432, 433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443, 444, 445, 446, 447, 448, 449, 450, 451, 452, 453, 454, 455, 456, 457, 458, 459, 460, 461, 462, 463, 464, 465, 466, 467, 468, 469, 470, 471, 472, 473, 474, 475, 476, 477, 478, 479, 480, 481, 482, 483, 484, 485, 486, 487);
    model.component("comp1").physics("cpt").feature("wall5").selection().all();
    model.component("comp1").physics("cpt").feature("wall5").selection()
         .set(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 293, 294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 353, 354, 355, 356, 357, 358, 359, 360, 361, 362, 363, 364, 365, 366, 367, 368, 369, 370, 371, 372, 373, 374, 375, 376, 377, 378, 379, 380, 381, 382, 383, 384, 385, 386, 387, 388, 389, 390, 391, 392, 393, 394, 395, 396, 397, 398, 399, 400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 419, 420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432, 433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443, 444, 445, 446, 447, 448, 449, 450, 451, 452, 453, 454, 455, 456, 457, 458, 459, 460, 461, 462, 463, 464, 465, 466, 467, 468, 469, 470, 471, 472, 473, 474, 475, 476, 477, 478, 479, 480, 481, 482, 483, 484, 485, 486, 487);

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.component("comp1").physics("cpt").feature("wall5").selection().set();

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(294);
    model.component("comp1").view("view1").hideEntities("hide1").add(329);
    model.component("comp1").view("view1").hideEntities("hide1").add(310);
    model.component("comp1").view("view1").hideEntities("hide1").add(59);
    model.component("comp1").view("view1").hideEntities("hide1").add(42);
    model.component("comp1").view("view1").hideEntities("hide1").add(408);
    model.component("comp1").view("view1").hideEntities("hide1").add(22);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(24);
    model.component("comp1").view("view1").hideEntities("hide1").add(41);
    model.component("comp1").view("view1").hideEntities("hide1").add(43);
    model.component("comp1").view("view1").hideEntities("hide1").add(14);
    model.component("comp1").view("view1").hideEntities("hide1").add(480);
    model.component("comp1").view("view1").hideEntities("hide1").add(485);
    model.component("comp1").view("view1").hideEntities("hide1").add(481);
    model.component("comp1").view("view1").hideEntities("hide1").add(479);
    model.component("comp1").view("view1").hideEntities("hide1").add(482);
    model.component("comp1").view("view1").hideEntities("hide1").add(40);
    model.component("comp1").view("view1").hideEntities("hide1").add(23);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);

    model.component("comp1").physics("cpt").feature("wall5").selection()
         .set(45, 46, 47, 190, 191, 219, 220, 221, 230, 231, 232, 295, 298, 324, 325, 328);

    model.component("comp1").view("view1").hideEntities("hide1").add(4);
    model.component("comp1").view("view1").hideEntities("hide1").add(25);
    model.component("comp1").view("view1").hideEntities("hide1").add(27);
    model.component("comp1").view("view1").hideEntities("hide1").add(28);
    model.component("comp1").view("view1").hideEntities("hide1").add(26);
    model.component("comp1").view("view1").hideEntities("hide1").add(487);
    model.component("comp1").view("view1").hideEntities("hide1").add(484);
    model.component("comp1").view("view1").hideEntities("hide1").add(486);

    model.component("comp1").physics("cpt").feature("wall5").selection()
         .set(45, 46, 47, 48, 190, 191, 192, 219, 220, 221, 223, 224, 225, 230, 231, 232, 295, 298, 299, 324, 325, 328);
    model.component("comp1").physics("es").feature("pot4").set("V0", 60);
    model.component("comp1").physics("es").feature("pot6").active(true);
    model.component("comp1").physics("es").feature("pot5").active(true);

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 35, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 768, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 837, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 116, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 70, 0);
    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("pp1").set("mp", "1.7e-22");

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 783, 0);
    model.result("pg3").run();

    model.component("comp1").physics("es").feature("pot4").set("V0", 70);
    model.component("comp1").physics("cpt").feature("pp1").set("mp", "1.7e-24");

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 258, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 6, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 18, 0);
    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("pp1").set("mp", "1.7e-26");

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 3, 0);
    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("pp1").set("mp", "1.7e-28");

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").run();

    model.component("comp1").physics("es").feature("pot4").active(false);
    model.component("comp1").physics("cpt").feature("pp1").set("mp", "1.7e-24");

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 118, 0);
    model.result("pg3").run();

    model.component("comp1").view("view1").set("showgrid", false);

    model.result("pg3").run();

    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4");
    model.component("comp1").view("view1").hideObjects("hide1").add("mov1(1)");
    model.component("comp1").view("view1").hideObjects("hide1").add("mov1(10)");
    model.component("comp1").view("view1").hideObjects("hide1").add("mov1(11)");
    model.component("comp1").view("view1").hideObjects("hide1").add("mov1(13)");
    model.component("comp1").view("view1").hideObjects("hide1").add("mov1(12)");

    model.result("pg1").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").run();

    model.component("comp1").view("view1").hideObjects().clear();

    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").run();

    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4");
    model.component("comp1").view("view1").hideObjects().clear();

    model.result("pg3").run();
    model.result("pg3").run();

    model.component("comp1").view("view1").camera().set("projection", "perspective");
    model.component("comp1").view("view1").set("transparency", true);
    model.component("comp1").view("view1").set("showgrid", false);

    model.result("pg3").set("showlegends", true);

    model.component("comp1").view("view1").set("scenelight", false);

    model.result("pg3").run();

    model.component("comp1").view("view1").camera().set("projection", "orthographic");

    model.result("pg3").setIndex("looplevel", 104, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 65, 0);
    model.result("pg3").run();

    model.label("lens8newMCP_shutter2.mph");

    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 13, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 14, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 20, 0);
    model.result("pg3").run();

    model.component("comp1").physics("es").feature("pot4").active(true);

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.component("comp1").physics("es").feature("pot5").active(false);
    model.component("comp1").physics("es").feature("pot6").active(false);

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.component("comp1").physics("es").feature("pot5").active(true);
    model.component("comp1").physics("es").feature("pot6").active(true);
    model.component("comp1").physics("es").feature("pot4").set("V0", -40);

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 30, 0);
    model.result("pg3").run();
    model.result("pg1").run();
    model.result().table("evl3")
         .addRow(new double[]{-1.1368683772161603E-13, -156.7952880859375, 270.5033264160156, -0.03056769499637252}, new double[]{0, 0, 0, 0});
    model.result("pg3").run();
    model.result("pg1").run();
    model.result("pg3").run();
    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").feature("slc1").set("rangecoloractive", false);
    model.result("pg3").run();

    model.component("comp1").geom("geom1").feature("cyl4").set("h", 2000);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("mov4").set("displz", 100);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("mov4").set("displz", 1050);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("mov3").set("displz", 1253);
    model.component("comp1").geom("geom1").runPre("fin");

    model.result("pg1").run();

    model.sol("sol1").study("std1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").attach("std1");

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size2").set("hauto", 3);
    model.component("comp1").mesh("mesh1").run();

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");

    return model;
  }

  public static Model run12(Model model) {
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.component("comp1").geom("geom1").feature("cyl4").set("h", 800);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("mov4").set("displz", 450);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("mov3").set("displz", 653);
    model.component("comp1").geom("geom1").runPre("fin");

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 43, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 88, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 119, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 161, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 273, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 214, 0);
    model.result("pg3").run();
    model.result("pg1").run();
    model.result("pg3").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 240, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 299, 0);
    model.result("pg3").run();

    model.component("comp1").geom("geom1").feature("mov4").set("displz", 50);
    model.component("comp1").geom("geom1").feature("mov3").set("displz", 253);
    model.component("comp1").geom("geom1").feature("cyl4").set("h", 400);
    model.component("comp1").geom("geom1").runPre("fin");

    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4");
    model.component("comp1").view("view1").hideObjects("hide1").add("mov1(1)");

    model.component("comp1").geom("geom1").run("dif8");
    model.component("comp1").geom("geom1").create("cyl20", "Cylinder");
    model.component("comp1").geom("geom1").feature("cyl20").set("r", 50);
    model.component("comp1").geom("geom1").feature("cyl20").set("pos", new int[]{0, 0, 100});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl20").set("r", 20);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl20").set("pos", new int[]{0, 0, 200});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl20").set("pos", new int[]{0, 0, 240});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl20").set("pos", new int[]{0, 0, 220});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();
    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.result("pg1").run();
    model.result("pg1").feature("slc1").set("rangecoloractive", true);
    model.result("pg1").feature("slc1").set("rangecolormin", -300);
    model.result("pg1").run();

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(335);
    model.component("comp1").view("view1").hideEntities("hide1").add(298);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);
    model.component("comp1").view("view1").hideEntities().create("hide2");
    model.component("comp1").view("view1").hideEntities("hide2").geom(3);
    model.component("comp1").view("view1").hideEntities("hide2").add(1);
    model.component("comp1").view("view1").hideEntities("hide2").add(2);

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.component("comp1").physics("es").create("pot7", "ElectricPotential", 2);
    model.component("comp1").physics("es").feature("pot7").selection().set(230, 231, 232, 233, 303, 330);
    model.component("comp1").physics("es").feature("pot7").set("V0", -200);

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.result("pg1").run();
    model.result("pg3").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.label("lens8newMCP_shutter4.mph");

    model.result("pg3").run();

    model.component("comp1").geom("geom1").feature("cyl4").label("Full Boundary Cylinder");
    model.component("comp1").geom("geom1").feature("imp2").active(true);
    model.component("comp1").geom("geom1").feature("cyl1").active(true);
    model.component("comp1").geom("geom1").feature("cyl3").active(true);
    model.component("comp1").geom("geom1").feature("dif1").active(true);
    model.component("comp1").geom("geom1").feature().remove("imp2");
    model.component("comp1").geom("geom1").feature().remove("cyl1");
    model.component("comp1").geom("geom1").feature().remove("cyl3");
    model.component("comp1").geom("geom1").feature().remove("dif1");
    model.component("comp1").geom("geom1").run("cyl2");
    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").feature("cyl2").label("Needle Tube");
    model.component("comp1").geom("geom1").feature("cone1").label("Needle Cone");
    model.component("comp1").geom("geom1").feature().remove("par1");

    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("fin");
    model.component("comp1").view("view1").hideObjects().clear();

    model.component("comp1").geom("geom1").run("cyl5");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl5").label("Lens Cylinder 1");
    model.component("comp1").geom("geom1").feature("cyl6").label("Lens Cylinder 2");
    model.component("comp1").geom("geom1").feature("cyl7").label("Lens Cylinder 3");
    model.component("comp1").geom("geom1").feature("cyl8").label("Lens Cylinder 4");
    model.component("comp1").geom("geom1").feature("dif2").label("Lens Difference 1");
    model.component("comp1").geom("geom1").feature("dif3").label("Lens Difference 2");
    model.component("comp1").geom("geom1").feature("dif4").label("Lens Difference 3");
    model.component("comp1").geom("geom1").run("cyl9");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl9").label("Lens Cylinder 5");
    model.component("comp1").geom("geom1").feature("cyl10").label("Lens Cylinder 6");
    model.component("comp1").geom("geom1").feature("dif5").label("Lens Difference 4");
    model.component("comp1").geom("geom1").feature("uni1").label("Lens Union 1");
    model.component("comp1").geom("geom1").feature("copy1").label("Lens Copy 1");
    model.component("comp1").geom("geom1").feature().remove("arr1");
    model.component("comp1").geom("geom1").feature().remove("cyl11");
    model.component("comp1").geom("geom1").feature().remove("cyl12");
    model.component("comp1").geom("geom1").feature().remove("arr2");
    model.component("comp1").geom("geom1").feature().remove("dif6");
    model.component("comp1").geom("geom1").feature().remove("cyl13");
    model.component("comp1").geom("geom1").feature().remove("imp3");
    model.component("comp1").geom("geom1").run("imp4");
    model.component("comp1").geom("geom1").feature("imp4").label("Import Chamber 1");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("rot1").label("Rotate Chamber 1");
    model.component("comp1").geom("geom1").feature("mov1").label("Move Chamber 1");
    model.component("comp1").geom("geom1").run("mov2");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("mov1");
    model.component("comp1").geom("geom1").run("mov2");
    model.component("comp1").geom("geom1").feature("mov2").label("Move Lens and Needles 1");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature().remove("cyl14");
    model.component("comp1").geom("geom1").feature().remove("cyl15");
    model.component("comp1").geom("geom1").run("mov2");
    model.component("comp1").geom("geom1").run("imp5");
    model.component("comp1").geom("geom1").feature("imp5").label("Import Ultem MCP Holder 5");
    model.component("comp1").geom("geom1").feature("mov3").label("Move MCP Holder 3");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("cyl16");
    model.component("comp1").geom("geom1").run("cyl17");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl16").label("MCP Cylinder 16");
    model.component("comp1").geom("geom1").feature("cyl17").label("MCP Cylinder 17");
    model.component("comp1").geom("geom1").feature("cyl18").label("MCP Cylinder 18");
    model.component("comp1").geom("geom1").feature("uni2").label("MCP Union 2");
    model.component("comp1").geom("geom1").feature("dif7").label("MCP Difference 7");
    model.component("comp1").geom("geom1").feature("mov4").label("MCP Move 4");
    model.component("comp1").geom("geom1").feature("cyl19").label("Fix MCP Holder Intefernce Cylinder 19");
    model.component("comp1").geom("geom1").feature("arr3").label("Array Four Posts 3");
    model.component("comp1").geom("geom1").feature("dif8").label("Difference MCP Holder and Trapeze 8");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("cyl20");
    model.component("comp1").geom("geom1").run("dif8");
    model.component("comp1").geom("geom1").run("cyl20");
    model.component("comp1").geom("geom1").feature("cyl20").label("Test Mesh Screen Cylinder 20");
    model.component("comp1").geom("geom1").run();

    model.component("comp1").material().remove("mat4");
    model.component("comp1").material().remove("mat6");

    model.component("comp1").physics("es").feature().remove("pot1");
    model.component("comp1").physics("es").feature().remove("pot2");
    model.component("comp1").physics("es").feature("pot3").label("Lens 1 Electric Potential 3");
    model.component("comp1").physics("es").feature("pot4").label("Lens 2 Electric Potential 4");
    model.component("comp1").physics("es").feature("pot3").label("Lens 1 Electric Potential");
    model.component("comp1").physics("es").feature("pot4").label("Lens 2 Electric Potential");
    model.component("comp1").physics("es").feature("pot5").label("MCP Front Electric Potential");
    model.component("comp1").physics("es").feature("pot6").label("MCP Back Electric Potential");
    model.component("comp1").physics("es").feature("pot7").label("Screen Mesh Electric Potential");
    model.component("comp1").physics("cpt").feature().remove("pbeam2");
    model.component("comp1").physics("cpt").feature().remove("inl1");
    model.component("comp1").physics("cpt").feature().remove("inl2");
    model.component("comp1").physics("cpt").feature("wall2").label("Lens Walls");
    model.component("comp1").physics("cpt").feature("wall4").label("Lens Walls 2");
    model.component("comp1").physics("cpt").feature("wall2").label("Lens Walls 1");
    model.component("comp1").physics("cpt").feature().remove("wall3");
    model.component("comp1").physics("cpt").feature("wall5").label("MCP and Holder Wall");

    model.component("comp1").mesh("mesh1").feature().remove("ftet5");
    model.component("comp1").mesh("mesh1").feature().remove("ftet6");
    model.component("comp1").mesh("mesh1").feature().remove("ftet3");

    model.result("pg2").run();
    model.result().remove("pg2");

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.component("comp1").physics("cpt").feature().remove("relg1");

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.sol("sol1").clearSolutionData();
    model.sol("sol2").clearSolutionData();

    model.component("comp1").geom("geom1").feature("cyl20").active(false);
    model.component("comp1").geom("geom1").run("cyl20");
    model.component("comp1").geom("geom1").create("cyl21", "Cylinder");
    model.component("comp1").geom("geom1").feature("cyl21").set("r", 3);
    model.component("comp1").geom("geom1").feature("cyl21").set("h", 19.9);
    model.component("comp1").geom("geom1").runPre("fin");

    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4");
    model.component("comp1").view("view1").hideObjects("hide1").add("mov1(1)");

    model.component("comp1").geom("geom1").feature("cyl21").set("pos", new int[]{20, 20, 0});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl21").set("pos", new int[]{24, 24, 0});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature().move("cyl21", 26);
    model.component("comp1").geom("geom1").runPre("mov4");
    model.component("comp1").geom("geom1").feature("mov4").selection("input").set("cyl21", "dif7");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").runPre("mov4");
    model.component("comp1").geom("geom1").feature("mov4").selection("input").set("dif7");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl21").set("pos", new int[]{24, 24, 100});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl21").set("pos", new int[]{24, 24, 200});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl21").set("pos", new int[]{24, 24, 230});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("cyl20");
    model.component("comp1").geom("geom1").create("arr4", "Array");
    model.component("comp1").geom("geom1").feature("arr4").selection("input").init();
    model.component("comp1").geom("geom1").feature("arr4").selection("input").set("cyl21");
    model.component("comp1").geom("geom1").feature("arr4").set("fullsize", new int[]{2, 2, 1});
    model.component("comp1").geom("geom1").feature("arr4").set("displ", new int[]{-48, -48, 0});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("arr4");
    model.component("comp1").geom("geom1").create("blk1", "Block");
    model.component("comp1").geom("geom1").feature("blk1").set("size", new int[]{12, 75, 3});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("blk1").set("base", "center");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("blk1").set("rot", 45);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("blk1").set("pos", new int[]{0, 0, 210});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("blk1").set("pos", new int[]{0, 0, 220});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("blk1").set("pos", new int[]{0, 0, 210});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("blk1").set("pos", new int[]{0, 0, 217});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("blk1").set("pos", new int[]{0, 0, 227});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("blk1").set("pos", new int[]{0, 0, 229});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("blk1").set("pos", new int[]{0, 0, 228});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature().duplicate("blk2", "blk1");
    model.component("comp1").geom("geom1").feature("blk2").set("rot", -45);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("blk2");
    model.component("comp1").geom("geom1").create("uni3", "Union");
    model.component("comp1").geom("geom1").feature("uni3").selection("input").set("blk1", "blk2");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("uni3");
    model.component("comp1").geom("geom1").create("cyl22", "Cylinder");
    model.component("comp1").geom("geom1").feature("cyl22").set("h", 3);
    model.component("comp1").geom("geom1").feature("cyl22").set("r", 6);
    model.component("comp1").geom("geom1").feature("cyl22").set("pos", new int[]{0, 0, 228});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl22").set("h", 5);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl22").set("pos", new int[]{0, 0, 227});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl22").set("pos", new int[]{0, 0, 226});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("cyl22");
    model.component("comp1").geom("geom1").create("dif9", "Difference");
    model.component("comp1").geom("geom1").feature("dif9").selection("input").set("uni3");
    model.component("comp1").geom("geom1").feature("dif9").selection("input2").set("cyl22");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("dif9");
    model.component("comp1").geom("geom1").create("cyl23", "Cylinder");
    model.component("comp1").geom("geom1").feature("cyl23").set("h", 0.8);
    model.component("comp1").geom("geom1").feature("cyl23").set("r", 12.4);
    model.component("comp1").geom("geom1").feature("cyl23").set("pos", new int[]{0, 0, 228});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl23").set("pos", new int[]{0, 0, 229});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl23").set("pos", new int[]{0, 0, 230});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl23").set("pos", new double[]{0, 0, 229.2});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").feature("cyl23").set("pos", new int[]{0, 0, 230});
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();
    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);

    model.component("comp1").material("mat5").selection().set(3, 20, 21, 33, 34);

    model.component("comp1").physics("es").feature("pot7").selection().all();
    model.component("comp1").physics("es").feature("pot7").selection().set(209, 213, 351, 365);

    model.component("comp1").selection().create("sel4", "Explicit");
    model.component("comp1").selection("sel4").set(17, 18, 24, 25, 26, 27, 30, 31, 32);

    model.component("comp1").physics("es").feature("pot7").selection().all();
    model.component("comp1").physics("es").feature("pot7").selection().named("sel2");
    model.component("comp1").physics("es").feature("pot7").selection().named("sel3");

    model.component("comp1").selection("sel4").geom("geom1", 3, 2, new String[]{"exterior"});

    return model;
  }

  public static Model run13(Model model) {
    model.component("comp1").selection("sel4").set(17, 18, 24, 25, 26, 27, 30, 31, 32);

    model.component("comp1").physics("es").feature("pot7").selection().named("sel4");

    model.component("comp1").selection().create("sel5", "Explicit");
    model.component("comp1").selection("sel5").set(17, 18, 25, 26, 27, 30, 31, 32);
    model.component("comp1").selection("sel5").geom("geom1", 3, 2, new String[]{"exterior"});
    model.component("comp1").selection("sel5").set(17, 18, 25, 26, 27, 30, 31, 32);

    model.component("comp1").physics("cpt").feature().duplicate("wall6", "wall5");
    model.component("comp1").physics("cpt").feature("wall6").selection().named("sel5");
    model.component("comp1").physics("cpt").feature("wall6").label("Mesh Holder");

    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size1").selection()
         .set(3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40);
    model.component("comp1").mesh("mesh1").run();

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.result("pg1").run();
    model.result("pg3").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.component("comp1").physics("es").feature("pot7").set("V0", -500);

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.component("comp1").physics("es").feature("pot7").set("V0", -1000);

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.component("comp1").physics("cpt").feature("pbeam1").set("N", 1000);

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.component("comp1").geom("geom1").feature().move("cyl21", 31);
    model.component("comp1").geom("geom1").feature("cyl21").label("Cylinder Screen Posts 21");
    model.component("comp1").geom("geom1").feature("cyl21").label("Cylinder Screen Post 21");
    model.component("comp1").geom("geom1").feature("arr4").label("Post Array 4");
    model.component("comp1").geom("geom1").feature("blk1").label("Cross Block 1");
    model.component("comp1").geom("geom1").feature("blk2").label("Cross Block 2");
    model.component("comp1").geom("geom1").feature("uni3").label("Cross Union 3");
    model.component("comp1").geom("geom1").feature("cyl22").label("Cross Cylinder Hole 22");
    model.component("comp1").geom("geom1").feature("dif9").label("Cross Difference 9");
    model.component("comp1").geom("geom1").feature("cyl23").label("Mesh Disc Cylinder 23");

    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4");
    model.component("comp1").view("view1").hideObjects("hide1").add("mov1(1)");

    model.label("lens8newMCP_screencross7.mph");

    model.component("comp1").geom("geom1").run("cyl16");
    model.component("comp1").geom("geom1").run("cyl18");
    model.component("comp1").geom("geom1").run("fin");

    model.label("lens8newMCP_screencross7_ks_v1.mph");

    model.result("pg1").run();

    model.label("lens8newMCP_screencross7_ks_v1.mph");

    model.result("pg1").run();

    model.component("comp1").geom("geom1").run("cyl16");
    model.component("comp1").geom("geom1").run("dif7");
    model.component("comp1").geom("geom1").feature("cyl16").active(false);
    model.component("comp1").geom("geom1").feature("cyl17").active(false);
    model.component("comp1").geom("geom1").feature("cyl18").active(false);
    model.component("comp1").geom("geom1").feature("uni2").active(false);
    model.component("comp1").geom("geom1").run("uni2");
    model.component("comp1").geom("geom1").run("uni2");
    model.component("comp1").geom("geom1").create("imp6", "Import");
    model.component("comp1").geom("geom1").feature("imp6")
         .set("filename", "C:\\Users\\kensh\\OneDrive - California Institute of Technology\\college files (onedrive)\\Roukes lab research\\ife mass spec 3d models\\electronics and mounting hardware\\hamamatsu mcp.SLDPRT");
    model.component("comp1").geom("geom1").run("uni2");
    model.component("comp1").geom("geom1").feature("cyl16").active(true);
    model.component("comp1").geom("geom1").feature("cyl17").active(true);
    model.component("comp1").geom("geom1").feature("cyl18").active(true);
    model.component("comp1").geom("geom1").feature("uni2").active(true);
    model.component("comp1").geom("geom1").feature().move("imp6", 21);
    model.component("comp1").geom("geom1").feature("imp6").label("import MCP model, do later");
    model.component("comp1").geom("geom1").feature("imp6").active(false);
    model.component("comp1").geom("geom1").run("fin");

    model.result("pg1").run();

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(381);
    model.component("comp1").view("view1").hideEntities("hide1").add(4);
    model.component("comp1").view("view1").hideEntities("hide1").add(334);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);
    model.component("comp1").view("view1").hideEntities("hide1").add(41);
    model.component("comp1").view("view1").hideEntities("hide1").add(26);
    model.component("comp1").view("view1").hideEntities("hide1").add(43);
    model.component("comp1").view("view1").hideEntities("hide1").add(28);
    model.component("comp1").view("view1").hideEntities("hide1").add(27);
    model.component("comp1").view("view1").hideEntities("hide1").add(314);
    model.component("comp1").view("view1").hideEntities("hide1").add(311);
    model.component("comp1").view("view1").hideEntities("hide1").add(310);
    model.component("comp1").view("view1").hideEntities("hide1").add(1);
    model.component("comp1").view("view1").hideEntities("hide1").add(312);
    model.component("comp1").view("view1").hideEntities("hide1").add(307);
    model.component("comp1").view("view1").hideEntities("hide1").add(313);
    model.component("comp1").view("view1").hideEntities("hide1").add(308);
    model.component("comp1").view("view1").hideEntities("hide1").add(309);
    model.component("comp1").view("view1").hideEntities("hide1").add(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(22);
    model.component("comp1").view("view1").hideEntities("hide1").add(24);
    model.component("comp1").view("view1").hideEntities("hide1").add(23);

    model.result().create("pg4", "PlotGroup2D");
    model.result("pg4").run();
    model.result().remove("pg4");
    model.result().create("pg4", "PlotGroup3D");
    model.result("pg4").run();
    model.result("pg4").label("initial beam spread");
    model.result("pg4").set("data", "part1");
    model.result("pg4").create("poma1", "PoincareMap");

    model.component("comp1").view("view1").set("showaxisorientation", true);

    model.result("pg4").run();
    model.result("pg4").run();
    model.result("pg4").feature("poma1").set("data", "parent");
    model.result("pg4").run();
    model.result().dataset().create("cpl1", "CutPlane");
    model.result().dataset("cpl1").set("data", "part1");
    model.result().dataset("cpl1").set("quickplane", "xy");
    model.result().dataset("cpl1").set("quickz", 2);

    model.component("comp1").geom("geom1").run("cyl2");
    model.component("comp1").geom("geom1").run("cyl5");
    model.component("comp1").geom("geom1").measure().selection().init();
    model.component("comp1").geom("geom1").measure().selection().set("cyl4(1)", "cyl2(1)", "cone1(1)", "cyl5(1)");
    model.component("comp1").geom("geom1").measure().selection().init();
    model.component("comp1").geom("geom1").measure().selection().set("cone1");
    model.component("comp1").geom("geom1").measure().selection().init();
    model.component("comp1").geom("geom1").measure().selection().set("cone1", "cyl2");
    model.component("comp1").geom("geom1").measure().selection().init();
    model.component("comp1").geom("geom1").measure().selection().set("cone1", "cyl2");
    model.component("comp1").geom("geom1").measure().selection().init();
    model.component("comp1").geom("geom1").measure().selection().set("cone1", "cyl2");
    model.component("comp1").geom("geom1").run("cone1");
    model.component("comp1").geom("geom1").run("cone1");
    model.component("comp1").geom("geom1").measure().selection().init(1);
    model.component("comp1").geom("geom1").measure().selection().set("cyl2", 3);
    model.component("comp1").geom("geom1").measure().selection().init(2);
    model.component("comp1").geom("geom1").measure().selection().all(new String[]{"cyl4(1)", "cyl2(1)", "cone1(1)"});
    model.component("comp1").geom("geom1").measure().selection().init(2);
    model.component("comp1").geom("geom1").measure().selection().set("cone1", 4);
    model.component("comp1").geom("geom1").measure().selection().set("cyl2", 3);
    model.component("comp1").geom("geom1").measure().selection().init(2);
    model.component("comp1").geom("geom1").measure().selection().set("cone1", 4);
    model.component("comp1").geom("geom1").measure().selection().set("cyl2", 3);
    model.component("comp1").geom("geom1").measure().selection().init(0);
    model.component("comp1").geom("geom1").measure().selection().set("cone1", 2);
    model.component("comp1").geom("geom1").measure().selection().set("cyl2", 1);
    model.component("comp1").geom("geom1").run("cyl2");
    model.component("comp1").geom("geom1").run("cone1");

    model.param().set("z_tip", "40[mm]");
    model.param().descr("z_tip", "z coordinate of tip where ions get released");

    model.result("pg4").run();
    model.result("pg4").run();
    model.result().remove("pg4");
    model.result().dataset("cpl1").set("quickz", "z_tip+2");

    model.component("comp1").geom("geom1").run("fin");

    model.result().dataset("cpl1").set("quickz", 42);
    model.result().dataset("cpl1").set("quickplane", "xy");
    model.result().dataset("cpl1").set("quickz", 108);
    model.result().dataset("cpl1").label("in front of tip");
    model.result().dataset("cpl1").set("quickz", 105);

    model.param().set("z_tip", "105[mm]");

    model.result().dataset("cpl1").set("quickz", "105+2");

    model.component("comp1").geom("geom1").run("arr3");
    model.component("comp1").geom("geom1").measure().selection().init();
    model.component("comp1").geom("geom1").measure().selection()
         .set("cyl4(1)", "mov1(1)", "mov1(2)", "mov1(3)", "mov1(4)", "mov1(5)", "mov1(6)", "mov1(7)", "mov1(8)", "mov1(9)", "mov1(10)", "mov1(11)", "mov1(12)", "mov1(13)", "mov1(14)", "mov1(15)", "mov1(16)", "mov1(17)", "mov2(1)", "mov2(2)", "mov2(3)", "mov2(4)", "mov3(1)", "mov4(1)", "arr3(1,1,1)", "arr3(2,1,1)", "arr3(1,2,1)", "arr3(2,2,1)");
    model.component("comp1").geom("geom1").measure().selection().init(1);
    model.component("comp1").geom("geom1").measure().selection().set("mov4", 14);
    model.component("comp1").geom("geom1").measure().selection().init(0);
    model.component("comp1").geom("geom1").measure().selection().set("mov4", 6, 20);
    model.component("comp1").geom("geom1").run("cyl17");
    model.component("comp1").geom("geom1").run("cyl18");
    model.component("comp1").geom("geom1").feature("cyl18").set("r", "42/2");
    model.component("comp1").geom("geom1").run("cyl18");
    model.component("comp1").geom("geom1").run("uni2");
    model.component("comp1").geom("geom1").run("dif7");
    model.component("comp1").geom("geom1").run("mov4");
    model.component("comp1").geom("geom1").run("cyl19");
    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").measureFinal().selection().geom("geom1", 2);
    model.component("comp1").geom("geom1").measureFinal().selection().set(333);
    model.component("comp1").geom("geom1").measureFinal().selection().geom("geom1", 2);
    model.component("comp1").geom("geom1").measureFinal().selection().set(333);
    model.component("comp1").geom("geom1").measureFinal().selection().geom("geom1");
    model.component("comp1").geom("geom1").measureFinal().selection().allGeom();
    model.component("comp1").geom("geom1").measureFinal().selection().geom("geom1", 2);
    model.component("comp1").geom("geom1").measureFinal().selection().set(254, 329);
    model.component("comp1").geom("geom1").measureFinal().selection().geom("geom1", 0);
    model.component("comp1").geom("geom1").measureFinal().selection().set(306, 379);

    model.param().set("z_mcp", "65+179.4[mm]");
    model.param().rename("z_tip", "tip_z");
    model.param().rename("z_mcp", "mcp_z");
    model.param().set("tip_base_z", "65[mm]");
    model.param().descr("tip_base_z", "z coord of tip base (for reference measurements)");
    model.param().descr("mcp_z", "z coord of mcp face");

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result().dataset("cpl1").set("quickz", "tip_z+2[mm]");
    model.result().dataset().duplicate("cpl2", "cpl1");
    model.result().dataset("cpl2").label("right before mcp");
    model.result().dataset("cpl2").set("quickz", "mcp_z-2[mm]");

    model.param().set("mcp_z", "65[mm]+179.4[mm]");

    model.result().dataset("cpl2").set("quickz", "0.244[m]-1[mm]");
    model.result().create("pg4", "PlotGroup3D");
    model.result("pg4").run();
    model.result("pg4").create("poma1", "PoincareMap");
    model.result("pg4").feature("poma1").set("data", "cpl1");
    model.result("pg4").feature("poma1").label("initial beam");
    model.result("pg4").run();
    model.result().create("pg5", "PlotGroup2D");
    model.result("pg5").run();
    model.result("pg5").create("poma1", "PoincareMap");
    model.result("pg5").feature("poma1").set("data", "cpl1");
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").create("poma2", "PoincareMap");
    model.result("pg5").feature("poma2").set("data", "cpl2");
    model.result("pg5").run();
    model.result("pg5").feature("poma2").label("Final Beam Cross Section");
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").feature("poma1").label("Initial Beam Cross Section");
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").feature("poma2").setIndex("looplevel", 991, 0);
    model.result("pg5").feature("poma2").setIndex("looplevel", 985, 0);
    model.result("pg5").run();
    model.result("pg5").feature("poma2").setIndex("looplevel", 1001, 0);
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").feature("poma2").set("data", "cpl1");
    model.result("pg5").run();
    model.result("pg5").feature("poma2").set("data", "cpl2");
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").feature("poma1").set("data", "none");
    model.result("pg5").run();
    model.result("pg5").feature("poma1").set("data", "cpl1");
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").label("beam profiles");
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").feature("poma2").setIndex("looplevel", 1000, 0);
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").feature("poma1").set("data", "cpl2");
    model.result("pg5").run();
    model.result("pg5").run();
    model.result().table().create("evl2", "Table");
    model.result().table("evl2").comments("Interactive 2D values");
    model.result().table("evl2").label("Evaluation 2D");
    model.result().table("evl2")
         .addRow(new double[]{-2.201284334211572, 1.852596794765792, 0}, new double[]{0, 0, 0});
    model.result().table("evl2")
         .addRow(new double[]{-0.26512008918240254, 0.41911519735654773, 0}, new double[]{0, 0, 0});
    model.result("pg4").run();
    model.result("pg4").run();
    model.result("pg4").feature().duplicate("poma2", "poma1");
    model.result("pg4").run();
    model.result("pg4").feature("poma2").label("final beam 1");
    model.result("pg4").feature("poma2").set("data", "cpl2");
    model.result("pg4").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").feature("poma2").setIndex("looplevel", 1001, 0);
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").feature("poma1").set("data", "cpl1");
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").feature("poma2").set("color", "blue");
    model.result("pg5").feature("poma2").create("col1", "Color");
    model.result("pg5").run();
    model.result("pg5").feature("poma2").feature("col1").set("expr", "cpt.Ek");
    model.result("pg5").feature("poma2").feature("col1").set("unit", "");
    model.result("pg5").run();
    model.result("pg5").feature("poma2").feature("col1").set("descractive", false);
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").feature("poma2").feature("col1").set("expr", "sqrt(cpt.vx^2+cpt.vy^2+cpt.vz^2)");
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg5").feature("poma1").create("col1", "Color");
    model.result("pg5").run();
    model.result("pg5").feature("poma1").feature("col1").set("expr", "sqrt(cpt.vx^2+cpt.vy^2+cpt.vz^2)");
    model.result("pg5").run();
    model.result("pg5").run();
    model.result().create("pg6", "PlotGroup2D");
    model.result("pg6").run();
    model.result("pg6").label("final beam profile");
    model.result("pg5").run();
    model.result("pg6").feature().copy("poma2", "pg5/poma2");
    model.result("pg5").feature().remove("poma2");
    model.result("pg5").run();
    model.result("pg5").label("initial beam profile");
    model.result("pg5").run();
    model.result("pg6").run();

    model.component("comp1").physics("cpt").feature("pbeam1").set("N", 100000);

    model.result("pg1").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg5").run();
    model.result("pg5").run();
    model.result("pg6").run();

    model.component("comp1").physics("cpt").feature("pbeam1").set("N", 1000);

    model.result("pg1").run();
    model.result("pg3").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").run();

    model.component("comp1").geom("geom1").run("cyl23");
    model.component("comp1").geom("geom1").run("blk1");

    model.label("lens8newMCP_screencross7_ks_v1.mph");

    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").run("cyl23");
    model.component("comp1").geom("geom1").measure().selection().init();
    model.component("comp1").geom("geom1").measure().selection()
         .set("cyl4(1)", "mov1(1)", "mov1(2)", "mov1(3)", "mov1(4)", "mov1(5)", "mov1(6)", "mov1(7)", "mov1(8)", "mov1(9)", "mov1(10)", "mov1(11)", "mov1(12)", "mov1(13)", "mov1(14)", "mov1(15)", "mov1(16)", "mov1(17)", "mov2(1)", "mov2(2)", "mov2(3)", "mov2(4)", "mov4(1)", "dif8(1)", "arr4(1,1,1)", "arr4(2,1,1)", "arr4(1,2,1)", "arr4(2,2,1)", "dif9(1)", "cyl23(1)");
    model.component("comp1").geom("geom1").measure().selection().init(0);
    model.component("comp1").geom("geom1").measure().selection().set("dif9", 19, 21);
    model.component("comp1").geom("geom1").feature("cyl22").set("r", 5.5);
    model.component("comp1").geom("geom1").run("cyl22");
    model.component("comp1").geom("geom1").run("cyl23");
    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").run("cyl23");

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");

    return model;
  }

  public static Model run14(Model model) {
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();
    model.result("pg3").run();
    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg3").run();
    model.result("pg1").run();

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();
    model.component("comp1").view("view1").set("transparency", true);
    model.component("comp1").view("view1").set("showaxisorientation", true);

    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").run("cyl7");
    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").run("fin");

    model.result("pg1").run();

    model.component("comp1").selection().create("sel6", "Explicit");
    model.component("comp1").selection().remove("sel6");
    model.component("comp1").selection().create("box1", "Box");

    model.result("pg5").run();
    model.result("pg6").run();
    model.result("pg4").run();
    model.result("pg3").run();

    model.component("comp1").selection().remove("box1");

    model.component("comp1").physics("es").feature("pot6").set("V0", -5000);

    model.component("comp1").geom("geom1").run("cyl23");
    model.component("comp1").geom("geom1").run("copy1");
    model.component("comp1").geom("geom1").run("imp4");
    model.component("comp1").geom("geom1").run("rot1");
    model.component("comp1").geom("geom1").run("mov1");
    model.component("comp1").geom("geom1").run("copy1");
    model.component("comp1").geom("geom1").run("copy1");
    model.component("comp1").geom("geom1").create("sel1", "ExplicitSelection");
    model.component("comp1").geom("geom1").feature("sel1").selection("selection").init(2);

    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init(2);
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4", 5);
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4", 1);
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4", 2);
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4", 6);

    model.component("comp1").geom("geom1").feature("sel1").selection("selection").set("copy1", 2, 31);
    model.component("comp1").geom("geom1").feature("sel1").set("groupcontang", true);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection").add("uni1", 20);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection").remove("uni1", 31);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection").add("uni1", 31);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection").add("uni1", 3);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection").add("uni1", 17);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection").remove("uni1", 17);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection").add("copy1", 10);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection").add("copy1", 8);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection").remove("copy1", 10);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection").add("copy1", 28);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection").remove("copy1", 13);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection").add("cyl4", 1, 2, 3, 4, 5, 6);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection").add("cyl2", 1, 2, 3, 4, 5, 6);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection").add("cone1", 1, 2, 3, 4, 5, 6);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection")
         .add("uni1", 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection")
         .add("copy1", 3, 4, 5, 6, 7, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 23, 24, 25, 26, 27, 28, 30);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection").remove("cyl2", 1);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection").remove("cone1", 1);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection").remove("cyl2", 4);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection").remove("copy1", 1);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection").remove("cyl4", 1, 2, 3, 4, 5, 6);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection").remove("cyl2", 3);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection").remove("cone1", 3, 4);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection")
         .remove("uni1", 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection")
         .remove("copy1", 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30);
    model.component("comp1").geom("geom1").feature().remove("sel1");
    model.component("comp1").geom("geom1").run("copy1");
    model.component("comp1").geom("geom1").create("boxsel1", "BoxSelection");
    model.component("comp1").geom("geom1").feature("boxsel1").set("entitydim", 2);
    model.component("comp1").geom("geom1").run("boxsel1");
    model.component("comp1").geom("geom1").feature("boxsel1").set("entitydim", 3);
    model.component("comp1").geom("geom1").feature("boxsel1").set("xmin", -10);
    model.component("comp1").geom("geom1").feature("boxsel1").set("xmax", 10);
    model.component("comp1").geom("geom1").feature("boxsel1").set("ymin", -10);
    model.component("comp1").geom("geom1").feature("boxsel1").set("ymax", 10);
    model.component("comp1").geom("geom1").feature("boxsel1").set("zmin", 10);
    model.component("comp1").geom("geom1").feature("boxsel1").set("zmax", 180);
    model.component("comp1").geom("geom1").run("boxsel1");
    model.component("comp1").geom("geom1").feature("boxsel1").set("zmax", 150);
    model.component("comp1").geom("geom1").feature("boxsel1").set("zmin", 90);
    model.component("comp1").geom("geom1").run("boxsel1");
    model.component("comp1").geom("geom1").feature("boxsel1").set("zmin", 92);
    model.component("comp1").geom("geom1").feature("boxsel1").set("ymax", 40);
    model.component("comp1").geom("geom1").feature("boxsel1").set("ymin", -40);
    model.component("comp1").geom("geom1").feature().move("boxsel1", 14);
    model.component("comp1").geom("geom1").feature("boxsel1").set("entitydim", 2);
    model.component("comp1").geom("geom1").feature("boxsel1").set("zmax", 130);
    model.component("comp1").geom("geom1").run("boxsel1");
    model.component("comp1").geom("geom1").feature("boxsel1").set("condition", "intersects");
    model.component("comp1").geom("geom1").feature("boxsel1").label("sel_lens_1");
    model.component("comp1").geom("geom1").run("boxsel1");
    model.component("comp1").geom("geom1").run("cone1");
    model.component("comp1").geom("geom1").run("cone1");
    model.component("comp1").geom("geom1").run("cone1");
    model.component("comp1").geom("geom1").create("sel1", "ExplicitSelection");
    model.component("comp1").geom("geom1").feature("sel1").selection("selection").set("cyl2", 1);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection").set("cone1", 1);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection").init(2);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection").init(3);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection").set("cyl2", 1);
    model.component("comp1").geom("geom1").feature("sel1").selection("selection").set("cone1", 1);
    model.component("comp1").geom("geom1").feature("sel1").label("sel_needle");
    model.component("comp1").geom("geom1").run("sel1");
    model.component("comp1").geom("geom1").run("boxsel1");
    model.component("comp1").geom("geom1").run("copy1");
    model.component("comp1").geom("geom1").run("copy1");
    model.component("comp1").geom("geom1").create("sel2", "ExplicitSelection");
    model.component("comp1").geom("geom1").feature("sel2").selection("selection").set("copy1", 1, 2);
    model.component("comp1").geom("geom1").feature("sel2").label("sel_lens_2");
    model.component("comp1").geom("geom1").run("sel2");
    model.component("comp1").geom("geom1").run("mov1");
    model.component("comp1").geom("geom1").run("imp4");

    model.component("comp1").view("view1").set("showgrid", true);

    model.component("comp1").geom("geom1").run("imp4");
    model.component("comp1").geom("geom1").create("boxsel2", "BoxSelection");
    model.component("comp1").geom("geom1").feature("boxsel2").set("xmax", -500);
    model.component("comp1").geom("geom1").feature("boxsel2").label("tube_chamber");
    model.component("comp1").geom("geom1").run("boxsel2");
    model.component("comp1").geom("geom1").run("mov4");

    model.component("comp1").view("view1").hideObjects().create("hide2");
    model.component("comp1").view("view1").hideObjects("hide2").init(3);
    model.component("comp1").view("view1").hideObjects("hide2").add("mov1(1)", 1);

    model.component("comp1").geom("geom1").run("cyl19");
    model.component("comp1").geom("geom1").run("mov4");
    model.component("comp1").geom("geom1").run("mov4");
    model.component("comp1").geom("geom1").create("sel3", "ExplicitSelection");
    model.component("comp1").geom("geom1").feature("sel3").selection("selection").init(2);
    model.component("comp1").geom("geom1").feature("sel3").selection("selection").set("mov4", 11);
    model.component("comp1").geom("geom1").feature("sel3").label("sel_mcp_front");
    model.component("comp1").geom("geom1").run("sel3");
    model.component("comp1").geom("geom1").run("sel3");
    model.component("comp1").geom("geom1").create("sel4", "ExplicitSelection");
    model.component("comp1").geom("geom1").feature("sel4").selection("selection").init(2);
    model.component("comp1").geom("geom1").feature("sel4").selection("selection").set("mov4", 4);
    model.component("comp1").geom("geom1").feature("sel4").label("sel_mcp_back");
    model.component("comp1").geom("geom1").run("sel4");
    model.component("comp1").geom("geom1").run("dif8");
    model.component("comp1").geom("geom1").run("dif8");
    model.component("comp1").geom("geom1").run("cyl23");
    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").run("cyl23");
    model.component("comp1").geom("geom1").feature("cyl23").set("r", 5.5);
    model.component("comp1").geom("geom1").run("cyl23");
    model.component("comp1").geom("geom1").feature("cyl23").set("r", 7);
    model.component("comp1").geom("geom1").run("cyl23");
    model.component("comp1").geom("geom1").run("cyl23");
    model.component("comp1").geom("geom1").create("sel5", "ExplicitSelection");
    model.component("comp1").geom("geom1").feature("sel5").selection("selection").set("cyl23", 1);
    model.component("comp1").geom("geom1").feature("sel5").label("sel_mesh");
    model.component("comp1").geom("geom1").run("sel5");
    model.component("comp1").geom("geom1").run("sel5");
    model.component("comp1").geom("geom1").create("sel6", "ExplicitSelection");
    model.component("comp1").geom("geom1").feature("sel6").selection("selection").set("dif9", 1, 2, 3, 4, 5);
    model.component("comp1").geom("geom1").feature("sel6").label("sel_mesh_cross");
    model.component("comp1").geom("geom1").run("sel6");
    model.component("comp1").geom("geom1").run();

    model.component("comp1").physics("es").feature("gnd1").selection().named("geom1_csel1_bnd");
    model.component("comp1").physics("es").feature("gnd1").selection().named("geom1_boxsel1");
    model.component("comp1").physics("es").feature("gnd1").selection().named("geom1_csel1_bnd");
    model.component("comp1").physics("es").feature("pot3").selection().named("geom1_boxsel1");
    model.component("comp1").physics("cpt").feature("wall4").selection().named("sel5");

    model.component("comp1").geom("geom1").run("sel2");
    model.component("comp1").geom("geom1").runPre("fin");

    model.component("comp1").physics("es").feature("pot5").selection().named("sel5");
    model.component("comp1").physics("es").feature("pot5").selection().named("geom1_sel3");
    model.component("comp1").physics("es").feature("pot6").selection().named("geom1_sel4");

    model.component("comp1").geom("geom1").feature("sel5").label("dom_mesh");
    model.component("comp1").geom("geom1").run("sel5");
    model.component("comp1").geom("geom1").feature("sel2").label("dom_lens_2");

    model.component("comp1").selection().create("adj1", "Adjacent");
    model.component("comp1").selection("adj1").label("sel_lens_2");
    model.component("comp1").selection("adj1").set("input", new String[]{"geom1_sel2"});

    model.component("comp1").physics("es").feature("pot4").selection().named("adj1");

    model.component("comp1").geom("geom1").feature("sel6").label("dom_mesh_cross");
    model.component("comp1").geom("geom1").run("sel6");

    model.component("comp1").selection().create("sel6", "Explicit");
    model.component("comp1").selection().remove("sel6");
    model.component("comp1").selection().create("adj2", "Adjacent");
    model.component("comp1").selection("adj2").label("sel_mesh_cross");
    model.component("comp1").selection("adj2").set("input", new String[]{"geom1_sel6"});

    model.component("comp1").physics("es").feature("pot7").selection().named("adj2");
    model.component("comp1").physics("es").feature().duplicate("pot8", "pot7");

    model.component("comp1").selection().create("adj3", "Adjacent");
    model.component("comp1").selection("adj3").label("sel_mesh");
    model.component("comp1").selection("adj3").set("input", new String[]{"geom1_sel5"});

    model.component("comp1").physics("es").feature("pot8").selection().named("adj3");

    model.component("comp1").selection().create("sel6", "Explicit");
    model.component("comp1").selection("sel6").geom(2);
    model.component("comp1").selection("sel6").set(325);
    model.component("comp1").selection("sel6").label("needle_tip");

    model.component("comp1").physics("cpt").feature("pbeam1").selection().named("sel6");
    model.component("comp1").physics("cpt").feature("wall2").selection().named("geom1_boxsel1");
    model.component("comp1").physics("cpt").feature("wall4").selection().named("adj1");
    model.component("comp1").physics("cpt").feature("wall6").selection().named("adj2");

    model.component("comp1").geom("geom1").run("sel4");
    model.component("comp1").geom("geom1").run("sel4");
    model.component("comp1").geom("geom1").run("sel4");
    model.component("comp1").geom("geom1").create("sel7", "ExplicitSelection");
    model.component("comp1").geom("geom1").feature("sel7").selection("selection").set("mov3", 1);
    model.component("comp1").geom("geom1").feature("sel7").selection("selection").set("mov4", 1, 2);
    model.component("comp1").geom("geom1").feature("sel7").label("dom_mcp_and_holder");
    model.component("comp1").geom("geom1").run("sel7");

    model.component("comp1").selection().create("adj4", "Adjacent");
    model.component("comp1").selection("adj4").label("sel_mcp_and_holder");
    model.component("comp1").selection("adj4").set("input", new String[]{"geom1_sel7"});

    model.component("comp1").physics("cpt").feature("wall5").selection().named("adj4");

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg3").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg1").run();

    model.component("comp1").physics("es").feature().duplicate("gnd2", "gnd1");
    model.component("comp1").physics("es").feature().move("gnd2", 4);

    model.component("comp1").geom("geom1").feature("sel1").label("dom_needle");

    model.component("comp1").selection().create("adj5", "Adjacent");
    model.component("comp1").selection("adj5").label("sel_needle");
    model.component("comp1").selection("adj5").set("input", new String[]{"geom1_sel1"});

    model.component("comp1").physics("es").feature("gnd2").selection().named("adj5");

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.component("comp1").geom("geom1").feature("sel4").selection("selection").init();
    model.component("comp1").geom("geom1").feature("sel4").selection("selection").init(2);
    model.component("comp1").geom("geom1").feature("sel4").selection("selection").set("mov4", 4);

    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg3").run();
    model.result("pg1").run();
    model.result().table("evl3")
         .addRow(new double[]{0, -0.26919843215057426, 101.1508360303715, -0.6420491816336376}, new double[]{0, 0, 0, 0});
    model.result().table("evl3")
         .addRow(new double[]{-0.8643443622468681, -1.4210854715202004E-14, 99.11422944456828, -23.459465135386374}, new double[]{0, 0, 0, 0});
    model.result().table("evl3")
         .addRow(new double[]{1.1368683772161603E-13, -6.173096644148643, 109.74146261918125, -118.61698227698854}, new double[]{0, 0, 0, 0});
    model.result().table("evl3")
         .addRow(new double[]{8.526512829121202E-14, -0.48392321452571707, 114.85605564569792, -113.18761683130222}, new double[]{0, 0, 0, 0});
    model.result().table("evl3")
         .addRow(new double[]{-2.0054901220438808, 4.263256414560601E-14, 105.5629979294265, -81.33803669994899}, new double[]{0, 0, 0, 0});
    model.result().table("evl3")
         .addRow(new double[]{-5.6843418860808015E-14, -0.2606787334933216, 105.45107954439263, -62.15303419674233}, new double[]{0, 0, 0, 0});

    model.label("lens8newMCP_screencross7_ks_v1.mph");

    model.result("pg3").run();
    model.result("pg1").run();

    model.component("comp1").geom("geom1").run("boxsel1");
    model.component("comp1").geom("geom1").feature("boxsel1").set("zmax", 100);
    model.component("comp1").geom("geom1").run("boxsel1");
    model.component("comp1").geom("geom1").feature("boxsel1").set("zmax", 130);
    model.component("comp1").geom("geom1").run("boxsel1");
    model.component("comp1").geom("geom1").feature("boxsel1").set("zmax", 120);
    model.component("comp1").geom("geom1").run("boxsel1");
    model.component("comp1").geom("geom1").feature("boxsel1").set("zmax", 110);
    model.component("comp1").geom("geom1").run("boxsel1");
    model.component("comp1").geom("geom1").run("sel2");
    model.component("comp1").geom("geom1").runPre("fin");

    model.component("comp1").selection("sel6").set("color", "12");

    model.component("comp1").geom("geom1").run("fin");

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.component("comp1").physics("es").feature("pot3").selection()
         .set(199, 200, 201, 202, 203, 204, 205, 206, 255, 256, 257, 258, 259, 260, 265, 266, 267, 268, 269, 270, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 295, 296, 297, 298, 328, 329, 332, 333, 334, 335, 336, 337, 338, 339, 346, 347, 352, 353, 360, 361, 362, 363, 364, 365, 366, 367, 370, 371);
    model.component("comp1").physics("es").feature("pot3").selection().named("geom1_boxsel1");

    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg3").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg5").run();
    model.result("pg6").run();
    model.result("pg5").run();
    model.result("pg6").run();
    model.result("pg5").run();
    model.result("pg6").run();
    model.result("pg5").run();
    model.result("pg6").run();
    model.result("pg5").run();
    model.result("pg6").run();
    model.result("pg5").run();
    model.result("pg6").run();
    model.result("pg5").run();
    model.result("pg6").run();

    return model;
  }

  public static Model run15(Model model) {
    model.result("pg4").run();
    model.result("pg4").run();
    model.result("pg6").run();
    model.result("pg5").run();
    model.result("pg6").run();
    model.result("pg5").run();
    model.result("pg6").run();

    model.component("comp1").geom("geom1").feature("imp6")
         .set("filename", "C:\\Users\\eiko\\OneDrive - California Institute of Technology\\college files (onedrive)\\Roukes lab research\\comsol_stuff\\mcp and in plane holder.STEP");
    model.component("comp1").geom("geom1").run("imp6");
    model.component("comp1").geom("geom1").feature("imp6").active(true);
    model.component("comp1").geom("geom1").run("imp6");
    model.component("comp1").geom("geom1").run("imp6");
    model.component("comp1").geom("geom1").create("mov5", "Move");
    model.component("comp1").geom("geom1").feature("mov5").selection("input")
         .set("imp6.BossExtrude10", "imp6.Chamfer1");
    model.component("comp1").geom("geom1").feature("mov5").set("specify", "pos");
    model.component("comp1").geom("geom1").feature("mov5").set("newpos", "coord");
    model.component("comp1").geom("geom1").feature("mov5").set("newposz", 100);
    model.component("comp1").geom("geom1").run("imp6");
    model.component("comp1").geom("geom1").feature("mov5").set("specify", "displ");
    model.component("comp1").geom("geom1").feature("mov5").set("displx", 1.5);
    model.component("comp1").geom("geom1").feature("mov5").set("displz", "");
    model.component("comp1").geom("geom1").feature("mov5").set("displx", 1500);
    model.component("comp1").geom("geom1").feature("mov5").set("displz", 1000);
    model.component("comp1").geom("geom1").run("mov5");
    model.component("comp1").geom("geom1").runPre("mov5");
    model.component("comp1").geom("geom1").feature("mov5").selection("input").set("imp6");
    model.component("comp1").geom("geom1").run("mov5");
    model.component("comp1").geom("geom1").feature("mov5").set("specify", "pos");
    model.component("comp1").geom("geom1").run("imp6");
    model.component("comp1").geom("geom1").run("imp6");
    model.component("comp1").geom("geom1").create("ls1", "LineSegment");
    model.component("comp1").geom("geom1").feature("ls1").selection("vertex1")
         .set("imp6.BossExtrude8", new int[]{4});
    model.component("comp1").geom("geom1").run("imp6");
    model.component("comp1").geom("geom1").feature("ls1").selection("vertex1")
         .set("imp6.BossExtrude8", new int[]{4});
    model.component("comp1").geom("geom1").feature("ls1").selection("vertex2").set("imp6.BossExtrude8", 2);
    model.component("comp1").geom("geom1").run("ls1");

    model.component("comp1").selection().create("cyl1", "Cylinder");
    model.component("comp1").selection().remove("cyl1");

    model.component("comp1").geom("geom1").run("ls1");
    model.component("comp1").geom("geom1").create("pt1", "Point");
    model.component("comp1").geom("geom1").feature().remove("pt1");
    model.component("comp1").geom("geom1").feature("mov5").set("newposx", 120);
    model.component("comp1").geom("geom1").run("ls1");
    model.component("comp1").geom("geom1").measure().selection().init(0);
    model.component("comp1").geom("geom1").measure().selection().set("imp6.BossExtrude10", 36);
    model.component("comp1").geom("geom1").feature().remove("ls1");
    model.component("comp1").geom("geom1").run("imp6");
    model.component("comp1").geom("geom1").create("wp1", "WorkPlane");
    model.component("comp1").geom("geom1").feature("wp1").set("unite", true);
    model.component("comp1").geom("geom1").feature("wp1").set("planetype", "faceparallel");
    model.component("comp1").geom("geom1").feature("wp1").selection("face").set("imp6.BossExtrude8", 4);
    model.component("comp1").geom("geom1").feature("wp1").selection("face").clear("imp6.BossExtrude8");
    model.component("comp1").geom("geom1").feature("wp1").selection("face").set("imp6.BossExtrude8", 3);
    model.component("comp1").geom("geom1").run("wp1");
    model.component("comp1").geom("geom1").feature("wp1").geom().create("pt1", "Point");
    model.component("comp1").geom("geom1").feature("wp1").geom().feature("pt1").label("mcp center");
    model.component("comp1").geom("geom1").feature("wp1").geom().run("pt1");
    model.component("comp1").geom("geom1").run("wp1");
    model.component("comp1").geom("geom1").create("par1", "Partition");
    model.component("comp1").geom("geom1").feature().remove("par1");
    model.component("comp1").geom("geom1").feature("mov5").selection("oldposvertex").set("wp1", 1);
    model.component("comp1").geom("geom1").feature("mov5").set("newposx", 0);
    model.component("comp1").geom("geom1").run("mov5");
    model.component("comp1").geom("geom1").feature("mov5").set("newposz", 200);
    model.component("comp1").geom("geom1").run("mov5");
    model.component("comp1").geom("geom1").feature("mov5").set("newposz", 300);
    model.component("comp1").geom("geom1").run("mov5");
    model.component("comp1").geom("geom1").feature("mov5").set("newposz", 250);
    model.component("comp1").geom("geom1").run("mov5");
    model.component("comp1").geom("geom1").feature("imp5").active(false);
    model.component("comp1").geom("geom1").feature("mov3").active(false);
    model.component("comp1").geom("geom1").run("mov5");
    model.component("comp1").geom("geom1").feature("cyl16").active(false);
    model.component("comp1").geom("geom1").feature("cyl17").active(false);
    model.component("comp1").geom("geom1").feature("cyl18").active(false);
    model.component("comp1").geom("geom1").feature("uni2").active(false);
    model.component("comp1").geom("geom1").feature("dif7").active(false);
    model.component("comp1").geom("geom1").feature("mov4").active(false);
    model.component("comp1").geom("geom1").run("sel4");
    model.component("comp1").geom("geom1").feature("sel3").selection("selection").set("mov5(1)", 3);
    model.component("comp1").geom("geom1").run("sel4");
    model.component("comp1").geom("geom1").feature("sel4").selection("selection").set("mov5(1)", 4);
    model.component("comp1").geom("geom1").run("sel4");
    model.component("comp1").geom("geom1").run("sel7");
    model.component("comp1").geom("geom1").feature("sel7").selection("selection").set("mov5(2)", 1);
    model.component("comp1").geom("geom1").feature("sel7").selection("selection").set("mov5(3)", 1);
    model.component("comp1").geom("geom1").run("sel7");
    model.component("comp1").geom("geom1").run("cyl19");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").runPre("dif8");
    model.component("comp1").geom("geom1").feature("dif8").selection("input").set("mov5(3)");
    model.component("comp1").geom("geom1").run("dif8");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run();

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();
    model.result("pg3").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.component("comp1").physics("es").feature("pot7").label("Screen Mesh Cross Electric Potential");

    model.result("pg3").run();
    model.result("pg6").run();
    model.result("pg5").run();
    model.result("pg6").run();
    model.result("pg1").run();
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 1001, 0);
    model.result("pg3").setIndex("looplevel", 974, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 140, 0);
    model.result("pg3").run();

    model.component("comp1").geom("geom1").run("sel7");
    model.component("comp1").geom("geom1").feature("sel7").selection("selection").set("mov5(1)", 1);
    model.component("comp1").geom("geom1").runPre("fin");

    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 119, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 47, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 34, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 7, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 30, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 23, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 34, 0);
    model.result("pg3").run();

    model.study("std2").feature("time").set("tlist", "range(0,1e-6,3e-5)");

    model.component("comp1").physics("cpt").create("wall7", "Wall", 2);
    model.component("comp1").physics("cpt").feature("wall7").selection().named("geom1_csel1_bnd");
    model.component("comp1").physics("cpt").feature("wall7").label("Chamber wall");

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.study("std2").feature("time").set("tlist", "range(0,1e-7,3e-5)");

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.component("comp1").geom("geom1").run("mov5");
    model.component("comp1").geom("geom1").run("wp1");
    model.component("comp1").geom("geom1").run("mov5");
    model.component("comp1").geom("geom1").runPre("mov5");
    model.component("comp1").geom("geom1").feature("mov5").selection("input").set("imp6", "wp1");
    model.component("comp1").geom("geom1").run("mov5");
    model.component("comp1").geom("geom1").runPre("fin");

    model.param().remove("mcp_z");
    model.param().set("mcp_z", "65[mm]+179.4[mm]");
    model.param().descr("mcp_z", "z coord of mcp face");
    model.param().set("mcp_z", "tip_base_z+55[mm]");

    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").run("cyl19");
    model.component("comp1").geom("geom1").run("cyl20");
    model.component("comp1").geom("geom1").run("cyl19");
    model.component("comp1").geom("geom1").feature("cyl19").set("pos", new String[]{"44.45", "44.45", "mcp_z"});
    model.component("comp1").geom("geom1").run("cyl19");
    model.component("comp1").geom("geom1").feature("mov5").label("Move mcp");
    model.component("comp1").geom("geom1").feature("mov5").set("newposz", "mcp_z");
    model.component("comp1").geom("geom1").run("mov5");

    model.param().set("mcp_z", "250[mm]");

    model.component("comp1").geom("geom1").run("mov5");
    model.component("comp1").geom("geom1").run("cyl20");
    model.component("comp1").geom("geom1").run("arr4");
    model.component("comp1").geom("geom1").run("cyl19");
    model.component("comp1").geom("geom1").run("cyl20");
    model.component("comp1").geom("geom1").run("cyl22");
    model.component("comp1").geom("geom1").run("cyl21");
    model.component("comp1").geom("geom1").run("uni3");
    model.component("comp1").geom("geom1").run("cyl22");
    model.component("comp1").geom("geom1").run("dif9");
    model.component("comp1").geom("geom1").run("cyl23");
    model.component("comp1").geom("geom1").run("dif8");
    model.component("comp1").geom("geom1").run("cyl21");
    model.component("comp1").geom("geom1").run("arr4");
    model.component("comp1").geom("geom1").run("blk1");
    model.component("comp1").geom("geom1").feature("cyl21").set("h", 20);
    model.component("comp1").geom("geom1").feature("cyl21").set("pos", new String[]{"24", "24", "z_mcp"});
    model.component("comp1").geom("geom1").run("cyl20");
    model.component("comp1").geom("geom1").feature("cyl21").set("pos", new String[]{"24", "24", "mcp_z"});
    model.component("comp1").geom("geom1").run("cyl21");
    model.component("comp1").geom("geom1").run("cyl21");
    model.component("comp1").geom("geom1").feature("cyl21").set("pos", new int[]{24, 24, 200});
    model.component("comp1").geom("geom1").run("cyl21");
    model.component("comp1").geom("geom1").feature("cyl21").set("pos", new String[]{"24", "24", "mcp_z"});
    model.component("comp1").geom("geom1").run("cyl21");
    model.component("comp1").geom("geom1").feature("cyl21").set("pos", new String[]{"24", "24", "mcp_z-10"});
    model.component("comp1").geom("geom1").run("cyl21");
    model.component("comp1").geom("geom1").feature("cyl21").set("pos", new String[]{"24", "24", "mcp_z-20"});
    model.component("comp1").geom("geom1").run("cyl21");
    model.component("comp1").geom("geom1").feature("cyl21").set("pos", new String[]{"24", "24", "mcp_z-10"});
    model.component("comp1").geom("geom1").run("cyl21");
    model.component("comp1").geom("geom1").feature("cyl21").set("pos", new String[]{"24", "24", "mcp_z-15"});
    model.component("comp1").geom("geom1").run("cyl21");
    model.component("comp1").geom("geom1").feature("cyl21").set("h", 10);
    model.component("comp1").geom("geom1").run("cyl21");
    model.component("comp1").geom("geom1").feature("cyl21").set("workplane", "wp1");
    model.component("comp1").geom("geom1").run("cyl21");
    model.component("comp1").geom("geom1").create("wp2", "WorkPlane");
    model.component("comp1").geom("geom1").feature("wp2").set("unite", true);
    model.component("comp1").geom("geom1").feature("wp2").set("planetype", "faceparallel");
    model.component("comp1").geom("geom1").feature("wp2").selection("face").set("mov5(2)", 15);
    model.component("comp1").geom("geom1").feature("wp2").label("mcp post base");
    model.component("comp1").geom("geom1").run("wp2");
    model.component("comp1").geom("geom1").feature().move("cyl21", 42);
    model.component("comp1").geom("geom1").feature("cyl21").set("workplane", "wp2");
    model.component("comp1").geom("geom1").feature("cyl21").set("pos", new int[]{24, 24, 0});
    model.component("comp1").geom("geom1").run("cyl21");
    model.component("comp1").geom("geom1").measure().selection().init();
    model.component("comp1").geom("geom1").measure().selection()
         .set("cyl4(1)", "mov1(1)", "mov1(2)", "mov1(3)", "mov1(4)", "mov1(5)", "mov1(6)", "mov1(7)", "mov1(8)", "mov1(9)", "mov1(10)", "mov1(11)", "mov1(12)", "mov1(13)", "mov1(14)", "mov1(15)", "mov1(16)", "mov1(17)", "mov2(1)", "mov2(2)", "mov2(3)", "mov2(4)", "mov5(1)", "mov5(2)", "mov5(4)", "dif8(1)", "cyl21(1)");
    model.component("comp1").geom("geom1").measure().selection().init(0);
    model.component("comp1").geom("geom1").measure().selection().set("mov5(2)", 19, 93);
    model.component("comp1").geom("geom1").run("cyl21");
    model.component("comp1").geom("geom1").run("wp2");
    model.component("comp1").geom("geom1").run("cyl21");
    model.component("comp1").geom("geom1").feature("cyl21").set("pos", new double[]{55.8, 55.8, 0});
    model.component("comp1").geom("geom1").run("cyl21");
    model.component("comp1").geom("geom1").runPre("wp2");
    model.component("comp1").geom("geom1").feature("wp2").selection("face").set("mov5(2)", new int[]{53});
    model.component("comp1").geom("geom1").run("wp2");
    model.component("comp1").geom("geom1").feature("wp2").selection("face").set("mov5(2)", new int[]{9});
    model.component("comp1").geom("geom1").feature("wp2").selection("face").clear("mov5(2)");
    model.component("comp1").geom("geom1").feature("wp2").selection("face").set("mov5(1)", new int[]{4});
    model.component("comp1").geom("geom1").run("wp2");
    model.component("comp1").geom("geom1").run("cyl21");
    model.component("comp1").geom("geom1").feature("cyl21").set("h", "-20");
    model.component("comp1").geom("geom1").run("wp2");
    model.component("comp1").geom("geom1").feature("cyl21").set("h", 20);
    model.component("comp1").geom("geom1").run("cyl21");
    model.component("comp1").geom("geom1").feature("wp2").set("reverse", true);
    model.component("comp1").geom("geom1").run("wp2");
    model.component("comp1").geom("geom1").run("cyl21");
    model.component("comp1").geom("geom1").feature("cyl21").set("pos", new double[]{27.9, 27.9, 0});
    model.component("comp1").geom("geom1").run("cyl21");
    model.component("comp1").geom("geom1").run("arr4");
    model.component("comp1").geom("geom1").feature("cyl21").set("pos", new int[]{28, 28, 0});
    model.component("comp1").geom("geom1").run("cyl21");
    model.component("comp1").geom("geom1").run("cyl21");
    model.component("comp1").geom("geom1").feature("arr4").set("displ", new int[]{28, 28, 0});
    model.component("comp1").geom("geom1").run("arr4");
    model.component("comp1").geom("geom1").feature("arr4").set("displ", new String[]{"28*2", "28", "0"});
    model.component("comp1").geom("geom1").run("arr4");
    model.component("comp1").geom("geom1").feature("arr4").set("displ", new String[]{"28*2", "28*2", "0"});
    model.component("comp1").geom("geom1").run("arr4");
    model.component("comp1").geom("geom1").run("blk1");
    model.component("comp1").geom("geom1").feature("blk1").set("pos", new String[]{"0", "0", ""});
    model.component("comp1").geom("geom1").feature("blk1").set("workplane", "wp2");
    model.component("comp1").geom("geom1").feature("blk1").set("pos", new int[]{0, 0, 20});
    model.component("comp1").geom("geom1").run("blk1");
    model.component("comp1").geom("geom1").feature("blk2").set("type", "surface");
    model.component("comp1").geom("geom1").feature("blk2").set("workplane", "wp2");
    model.component("comp1").geom("geom1").feature("blk2").set("pos", new int[]{0, 0, 20});
    model.component("comp1").geom("geom1").run("blk2");
    model.component("comp1").geom("geom1").feature("blk2").set("size", new int[]{12, 90, 3});
    model.component("comp1").geom("geom1").run("blk2");
    model.component("comp1").geom("geom1").feature("blk1").set("size", new int[]{12, 90, 3});
    model.component("comp1").geom("geom1").run("blk1");
    model.component("comp1").geom("geom1").run("uni3");
    model.component("comp1").geom("geom1").run("cyl22");
    model.component("comp1").geom("geom1").run("cyl23");
    model.component("comp1").geom("geom1").feature("cyl22").set("workplane", "wp2");
    model.component("comp1").geom("geom1").feature("cyl22").set("pos", new int[]{0, 0, 20});
    model.component("comp1").geom("geom1").run("cyl22");
    model.component("comp1").geom("geom1").feature("cyl22").set("pos", new int[]{0, 0, 15});
    model.component("comp1").geom("geom1").run("cyl22");
    model.component("comp1").geom("geom1").feature("cyl22").set("h", 10);
    model.component("comp1").geom("geom1").run("cyl22");
    model.component("comp1").geom("geom1").run("dif9");
    model.component("comp1").geom("geom1").run("cyl23");
    model.component("comp1").geom("geom1").feature("cyl23").set("workplane", "wp2");
    model.component("comp1").geom("geom1").feature("cyl23").set("pos", new int[]{0, 0, 18});
    model.component("comp1").geom("geom1").run("cyl23");
    model.component("comp1").geom("geom1").feature("cyl23").set("h", 0.2);
    model.component("comp1").geom("geom1").run("cyl23");
    model.component("comp1").geom("geom1").feature("cyl23").set("pos", new int[]{0, 0, 20});
    model.component("comp1").geom("geom1").feature("cyl23").set("h", 10);
    model.component("comp1").geom("geom1").run("cyl23");
    model.component("comp1").geom("geom1").feature("cyl23").set("axistype", "x");
    model.component("comp1").geom("geom1").feature("cyl23").set("h", "-10");
    model.component("comp1").geom("geom1").run("dif9");
    model.component("comp1").geom("geom1").feature("cyl23").set("h", "");
    model.component("comp1").geom("geom1").run("dif9");
    model.component("comp1").geom("geom1").feature("cyl23").set("h", 0.2);
    model.component("comp1").geom("geom1").run("cyl23");
    model.component("comp1").geom("geom1").feature("cyl23").set("axistype", "z");
    model.component("comp1").geom("geom1").run("cyl23");
    model.component("comp1").geom("geom1").feature("cyl23").set("pos", new int[]{0, 0, 18});
    model.component("comp1").geom("geom1").run("cyl23");
    model.component("comp1").geom("geom1").feature("cyl23").set("pos", new double[]{0, 0, 18.5});
    model.component("comp1").geom("geom1").run("cyl23");
    model.component("comp1").geom("geom1").run("cyl23");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run();
    model.component("comp1").geom("geom1").run("sel6");
    model.component("comp1").geom("geom1").run("sel5");
    model.component("comp1").geom("geom1").feature("sel6").selection("selection").set("dif9", 3);
    model.component("comp1").geom("geom1").feature("sel6").selection("selection").clear("dif9");
    model.component("comp1").geom("geom1").feature("sel6").selection("selection").set("dif9", 1, 2, 3);
    model.component("comp1").geom("geom1").run("sel6");
    model.component("comp1").geom("geom1").run("blk2");
    model.component("comp1").geom("geom1").run("blk1");
    model.component("comp1").geom("geom1").run("blk2");
    model.component("comp1").geom("geom1").run("sel6");
    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").run("cyl23");
    model.component("comp1").geom("geom1").feature("sel6").selection("selection").init();
    model.component("comp1").geom("geom1").feature("sel6").selection("selection").set("dif9");
    model.component("comp1").geom("geom1").run("sel6");
    model.component("comp1").geom("geom1").feature("sel6").selection("selection").init(3);
    model.component("comp1").geom("geom1").feature("sel6").selection("selection").init();
    model.component("comp1").geom("geom1").feature("sel6").selection("selection").set("dif9");
    model.component("comp1").geom("geom1").run("sel6");

    model.component("comp1").selection("adj2").set("entitydim", 3);
    model.component("comp1").selection("adj2").set("input", new String[]{"geom1_sel6_dom"});

    model.component("comp1").geom("geom1").run("sel6");
    model.component("comp1").geom("geom1").run("sel6");
    model.component("comp1").geom("geom1").runPre("sel6");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").run("sel6");
    model.component("comp1").geom("geom1").feature("sel6").selection("selection").init(3);
    model.component("comp1").geom("geom1").run("blk1");
    model.component("comp1").geom("geom1").feature("blk2").set("type", "solid");
    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").run("sel6");
    model.component("comp1").geom("geom1").feature("sel6").selection("selection").set("dif9", 1, 2, 3, 4, 5);
    model.component("comp1").geom("geom1").run("sel6");
    model.component("comp1").geom("geom1").run("fin");

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.param().set("cfg", "2");
    model.param().set("z_c2", "if(cfg==3,L_c1,0)");
    model.param().remove("z_c2");
    model.param().set("z_c2", "if(cfg==3,L_c1,0)");
    model.param().descr("z_c2", "");
    model.param().remove("z_c2");

    model.component("comp1").geom("geom1").run("mov2");
    model.component("comp1").geom("geom1").run("mov1");
    model.component("comp1").geom("geom1").run("mov1");
    model.component("comp1").geom("geom1").create("imp7", "Import");
    model.component("comp1").geom("geom1").feature("imp7")
         .set("filename", "C:\\Users\\eiko\\OneDrive - California Institute of Technology\\college files (onedrive)\\Roukes lab research\\comsol_stuff\\sphere chamber 10 in flange at 7 in.STEP");
    model.component("comp1").geom("geom1").run("imp7");
    model.component("comp1").geom("geom1").run("imp7");
    model.component("comp1").geom("geom1").create("rt1", "RigidTransform");
    model.component("comp1").geom("geom1").feature("rt1").set("axistype", "y");
    model.component("comp1").geom("geom1").feature("rt1").set("rot", 90);
    model.component("comp1").geom("geom1").run("imp7");
    model.component("comp1").geom("geom1").feature("rt1").selection("input").set("imp7.Sphere1");
    model.component("comp1").geom("geom1").run("rt1");
    model.component("comp1").geom("geom1").runPre("rt1");
    model.component("comp1").geom("geom1").feature("rt1").selection("input").init();
    model.component("comp1").geom("geom1").feature("imp7").label("Import Chambe 2");
    model.component("comp1").geom("geom1").feature("rt1").selection("input").set("imp7.Sphere1");
    model.component("comp1").geom("geom1").feature("rt1").selection("input").init();
    model.component("comp1").geom("geom1").feature("imp7").set("keepbnd", false);
    model.component("comp1").geom("geom1").run("imp7");
    model.component("comp1").geom("geom1").feature("rt1").selection("input").set("imp7.Sphere1");
    model.component("comp1").geom("geom1").feature("rt1").set("displ", new int[]{300, 0, 0});
    model.component("comp1").geom("geom1").run("cyl4");
    model.component("comp1").geom("geom1").run("cyl2");
    model.component("comp1").geom("geom1").run("cone1");
    model.component("comp1").geom("geom1").run("rt1");
    model.component("comp1").geom("geom1").runPre("rt1");
    model.component("comp1").geom("geom1").feature("rt1").selection("input").init();
    model.component("comp1").geom("geom1").feature().move("imp4", 1);
    model.component("comp1").geom("geom1").feature().move("boxsel2", 2);
    model.component("comp1").geom("geom1").feature().move("rot1", 3);
    model.component("comp1").geom("geom1").feature().move("mov1", 4);
    model.component("comp1").geom("geom1").feature().move("imp7", 5);
    model.component("comp1").geom("geom1").feature().move("rt1", 6);
    model.component("comp1").geom("geom1").feature("imp7").label("Import Chamber 2");
    model.component("comp1").geom("geom1").run("imp7");
    model.component("comp1").geom("geom1").run("boxsel2");
    model.component("comp1").geom("geom1").run("imp7");

    model.component("comp1").view("view1").hideObjects().clear();

    model.component("comp1").geom("geom1").run("imp7");

    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4");

    model.component("comp1").geom("geom1").measure().selection().init();
    model.component("comp1").geom("geom1").measure().selection()
         .set("cyl4(1)", "mov1(1)", "mov1(2)", "mov1(3)", "mov1(4)", "mov1(5)", "mov1(6)", "mov1(7)", "mov1(8)", "mov1(9)", "mov1(10)", "mov1(11)", "mov1(12)", "mov1(13)", "mov1(14)", "mov1(15)", "mov1(16)", "mov1(17)", "imp7.Sphere1", "imp7.Port_A_Flange1", "imp7.Port_B_Flange1", "imp7.Port_C_Flange1", "imp7.Port_D_Flange1", "imp7.Port_E_Flange1", "imp7.Port_F_Flange1", "imp7.Port_G_Flange1", "imp7.Port_H_Flange1", "imp7.Port_I_Flange1", "imp7.Port_J_Flange1", "imp7.Port_K_Flange1", "imp7.Port_L_Flange1", "imp7.Port_M_Flange1", "imp7.Port_N_Flange1", "imp7.Port_O_Flange1", "imp7.Port_P_Flange1");
    model.component("comp1").geom("geom1").measure().selection().init(0);

    return model;
  }

  public static Model run16(Model model) {
    model.component("comp1").geom("geom1").measure().selection().set("mov1(1)", 116);
    model.component("comp1").geom("geom1").run("mov1");
    model.component("comp1").geom("geom1").run("mov1");
    model.component("comp1").geom("geom1").create("par1", "Partition");
    model.component("comp1").geom("geom1").feature("par1").selection("input").set("mov1(1)");
    model.component("comp1").geom("geom1").feature().remove("par1");
    model.component("comp1").geom("geom1").run("boxsel2");
    model.component("comp1").geom("geom1").feature("boxsel2").set("entitydim", -1);
    model.component("comp1").geom("geom1").feature("boxsel2").set("inputent", "selections");
    model.component("comp1").geom("geom1").feature().remove("boxsel2");
    model.component("comp1").geom("geom1").run("imp4");
    model.component("comp1").geom("geom1").create("sel8", "ExplicitSelection");
    model.component("comp1").geom("geom1").feature("sel8").selection("selection").init();
    model.component("comp1").geom("geom1").feature("sel8").selection("selection").set("imp4.Body1(1)");
    model.component("comp1").geom("geom1").feature("sel8").label("Tube Chamber 1");
    model.component("comp1").geom("geom1").run("sel8");
    model.component("comp1").geom("geom1").run("sel8");
    model.component("comp1").geom("geom1").run("mov1");
    model.component("comp1").geom("geom1").run("imp7");
    model.component("comp1").geom("geom1").run("imp7");
    model.component("comp1").geom("geom1").create("sel9", "ExplicitSelection");
    model.component("comp1").geom("geom1").feature("sel9").selection("selection").init();
    model.component("comp1").geom("geom1").feature("imp7").set("keepbnd", true);
    model.component("comp1").geom("geom1").feature("imp7").set("fillholes", false);
    model.component("comp1").geom("geom1").run("imp7");
    model.component("comp1").geom("geom1").feature("sel9").selection("selection").set("imp7.Sphere1");
    model.component("comp1").geom("geom1").feature().move("imp7", 1);
    model.component("comp1").geom("geom1").feature().move("sel9", 2);
    model.component("comp1").geom("geom1").feature().move("rt1", 3);
    model.component("comp1").geom("geom1").feature().move("cyl4", 3);
    model.component("comp1").geom("geom1").runPre("sel9");
    model.component("comp1").geom("geom1").feature().remove("sel9");
    model.component("comp1").geom("geom1").run("imp7");
    model.component("comp1").geom("geom1").create("boxsel2", "BoxSelection");
    model.component("comp1").geom("geom1").feature("boxsel2").set("entitydim", -1);
    model.component("comp1").geom("geom1").run("boxsel2");
    model.component("comp1").geom("geom1").create("uni4", "Union");
    model.component("comp1").geom("geom1").feature("uni4").selection("input").named("csel1");
    model.component("comp1").geom("geom1").feature("uni4").selection("input").named("");
    model.component("comp1").geom("geom1").feature("uni4").selection("input").named("boxsel2");
    model.component("comp1").geom("geom1").feature("uni4").label("Chamber 2 Union");
    model.component("comp1").geom("geom1").run("uni4");
    model.component("comp1").geom("geom1").feature("boxsel2").label("Sphere Chamber 2");
    model.component("comp1").geom("geom1").run("boxsel2");
    model.component("comp1").geom("geom1").feature("imp7").set("selresult", true);
    model.component("comp1").geom("geom1").feature("imp7").set("color", "4");
    model.component("comp1").geom("geom1").run("imp7");
    model.component("comp1").geom("geom1").feature("imp7").set("color", "none");
    model.component("comp1").geom("geom1").run("imp7");
    model.component("comp1").geom("geom1").run("imp7");
    model.component("comp1").geom("geom1").run("imp7");
    model.component("comp1").geom("geom1").run("boxsel2");
    model.component("comp1").geom("geom1").feature("uni4").selection("input").named("imp7");
    model.component("comp1").geom("geom1").run("uni4");
    model.component("comp1").geom("geom1").feature().move("boxsel2", 2);
    model.component("comp1").geom("geom1").feature().remove("boxsel2");
    model.component("comp1").geom("geom1").run("uni4");
    model.component("comp1").geom("geom1").create("sel9", "ExplicitSelection");
    model.component("comp1").geom("geom1").feature("sel9").selection("selection").init();
    model.component("comp1").geom("geom1").feature("sel9").selection("selection").set("uni4");
    model.component("comp1").geom("geom1").feature("sel9").label("Spherical Chamber 2");
    model.component("comp1").geom("geom1").run("sel9");
    model.component("comp1").geom("geom1").feature("rt1").selection("input").set("uni4");
    model.component("comp1").geom("geom1").run("rt1");
    model.component("comp1").geom("geom1").feature("rt1").set("displ", new int[]{0, 0, 0});
    model.component("comp1").geom("geom1").feature("rt1").set("axistype", "x");
    model.component("comp1").geom("geom1").run("rt1");
    model.component("comp1").geom("geom1").run("rot1");
    model.component("comp1").geom("geom1").run("mov1");
    model.component("comp1").geom("geom1").run("mov1");
    model.component("comp1").geom("geom1").run("sel9");
    model.component("comp1").geom("geom1").feature("rt1").set("axistype", "y");
    model.component("comp1").geom("geom1").feature("rt1").set("rot", -90);
    model.component("comp1").geom("geom1").run("rt1");
    model.component("comp1").geom("geom1").feature("rt1").set("rot", 270);
    model.component("comp1").geom("geom1").run("rt1");
    model.component("comp1").geom("geom1").run("sel8");
    model.component("comp1").geom("geom1").run("cyl2");
    model.component("comp1").geom("geom1").feature("rt1").set("rot", 90);
    model.component("comp1").geom("geom1").run("rt1");
    model.component("comp1").geom("geom1").run("cyl2");
    model.component("comp1").geom("geom1").feature("uni4").set("intbnd", false);
    model.component("comp1").geom("geom1").run("uni4");
    model.component("comp1").geom("geom1").run("cyl4");
    model.component("comp1").geom("geom1").run("mov1");
    model.component("comp1").geom("geom1").measure().selection().init();
    model.component("comp1").geom("geom1").measure().selection()
         .set("rt1(1)", "cyl4(1)", "mov1(1)", "mov1(2)", "mov1(3)", "mov1(4)", "mov1(5)", "mov1(6)", "mov1(7)", "mov1(8)", "mov1(9)", "mov1(10)", "mov1(11)", "mov1(12)", "mov1(13)", "mov1(14)", "mov1(15)", "mov1(16)", "mov1(17)");
    model.component("comp1").geom("geom1").measure().selection().init(0);
    model.component("comp1").geom("geom1").measure().selection().set("mov1(1)", 116);
    model.component("comp1").geom("geom1").run("mov1");
    model.component("comp1").geom("geom1").run("imp4");
    model.component("comp1").geom("geom1").run("rot1");
    model.component("comp1").geom("geom1").run("mov1");

    model.component("comp1").view("view1").hideObjects().clear();

    model.component("comp1").geom("geom1").run("rot1");
    model.component("comp1").geom("geom1").run("rot1");
    model.component("comp1").geom("geom1").create("wp3", "WorkPlane");
    model.component("comp1").geom("geom1").feature("wp3").set("unite", true);
    model.component("comp1").geom("geom1").feature("wp3").set("planetype", "faceparallel");
    model.component("comp1").geom("geom1").feature("wp3").selection("face").set("rot1(1)", 76);
    model.component("comp1").geom("geom1").feature("wp3").set("reverse", true);
    model.component("comp1").geom("geom1").feature("wp3").label("input plane");
    model.component("comp1").geom("geom1").run("wp3");
    model.component("comp1").geom("geom1").run("wp3");
    model.component("comp1").geom("geom1").feature("wp3").geom().create("pt1", "Point");
    model.component("comp1").geom("geom1").feature("wp3").geom().feature("pt1").label("input center");
    model.component("comp1").geom("geom1").feature("wp3").geom().run("pt1");
    model.component("comp1").geom("geom1").feature("mov1").set("specify", "pos");
    model.component("comp1").geom("geom1").runPre("mov1");
    model.component("comp1").geom("geom1").feature("mov1").selection("input").set("rot1", "wp3");
    model.component("comp1").geom("geom1").run("wp3");
    model.component("comp1").geom("geom1").feature("mov1").selection("oldposvertex").set("wp3", 1);
    model.component("comp1").geom("geom1").feature("mov1").set("newpos", "coord");
    model.component("comp1").geom("geom1").run("mov1");
    model.component("comp1").geom("geom1").run("rt1");
    model.component("comp1").geom("geom1").run("rt1");
    model.component("comp1").geom("geom1").create("wp4", "WorkPlane");
    model.component("comp1").geom("geom1").feature("wp4").set("unite", true);
    model.component("comp1").geom("geom1").feature("wp4").set("planetype", "edgeparallel");
    model.component("comp1").geom("geom1").feature("wp4").selection("planaredge").set("rt1", 2356);
    model.component("comp1").geom("geom1").feature("wp4").set("planetype", "circleperpendicular");
    model.component("comp1").geom("geom1").feature("wp4").selection("circedge").set("rt1", 2356);
    model.component("comp1").geom("geom1").feature("wp4").set("planetype", "faceparallel");
    model.component("comp1").geom("geom1").feature("wp4").selection("face").set("rt1", new int[]{878});
    model.component("comp1").geom("geom1").run("wp4");
    model.component("comp1").geom("geom1").feature("wp4").geom().create("c1", "Circle");
    model.component("comp1").geom("geom1").feature("wp4").geom().run("c1");
    model.component("comp1").geom("geom1").feature("wp4").geom().create("c2", "Circle");
    model.component("comp1").geom("geom1").feature("wp4").geom().feature().remove("c2");
    model.component("comp1").geom("geom1").feature("wp4").set("workplane3d", false);
    model.component("comp1").geom("geom1").feature("wp4").geom().feature().remove("c1");
    model.component("comp1").geom("geom1").feature("wp4").selection("face").set("rt1", new int[]{870});
    model.component("comp1").geom("geom1").feature("wp4").geom().create("pt1", "Point");
    model.component("comp1").geom("geom1").feature("wp4").geom().feature("pt1")
         .label("input flange center slightly inward");
    model.component("comp1").geom("geom1").feature("wp4").geom().run("pt1");
    model.component("comp1").geom("geom1").feature("wp4").label("chamber 2 input flange");
    model.component("comp1").geom("geom1").run("wp4");
    model.component("comp1").geom("geom1").run("cyl4");
    model.component("comp1").geom("geom1").measure().selection().init(2);
    model.component("comp1").geom("geom1").measure().selection().all(new String[]{"rt1(1)", "wp4.pt1", "cyl4(1)"});
    model.component("comp1").geom("geom1").measure().selection().init(2);
    model.component("comp1").geom("geom1").measure().selection().set("rt1", 870, 878);
    model.component("comp1").geom("geom1").measure().selection().init(1);
    model.component("comp1").geom("geom1").measure().selection().set("rt1", 2308, 2329);
    model.component("comp1").geom("geom1").measure().selection().init(1);
    model.component("comp1").geom("geom1").measure().selection().set("rt1", 2309);
    model.component("comp1").geom("geom1").run("wp4");
    model.component("comp1").geom("geom1").run("wp4");
    model.component("comp1").geom("geom1").create("mov6", "Move");
    model.component("comp1").geom("geom1").feature("mov6").selection("input").named("imp7");
    model.component("comp1").geom("geom1").feature("mov6").selection("input").set("rt1", "wp4");
    model.component("comp1").geom("geom1").feature("mov6").selection("input").named("sel9");
    model.component("comp1").geom("geom1").feature("mov6").selection("input").set("rt1", "wp4");
    model.component("comp1").geom("geom1").feature("mov6").set("specify", "pos");
    model.component("comp1").geom("geom1").feature("mov6").selection("oldposvertex").set("wp4", 1);
    model.component("comp1").geom("geom1").feature("mov6").set("newpos", "coord");
    model.component("comp1").geom("geom1").feature("mov6").set("newposz", 1.1684);
    model.component("comp1").geom("geom1").run("mov6");
    model.component("comp1").geom("geom1").measure().selection().init(0);
    model.component("comp1").geom("geom1").measure().selection().set("mov6(1)", 1498);
    model.component("comp1").geom("geom1").run("wp3");
    model.component("comp1").geom("geom1").run("mov1");
    model.component("comp1").geom("geom1").run("wp4");
    model.component("comp1").geom("geom1").run("wp4");
    model.component("comp1").geom("geom1").create("uni5", "Union");
    model.component("comp1").geom("geom1").feature("uni5").selection("input").set("rt1");
    model.component("comp1").geom("geom1").feature("uni5").selection("input").named("sel9");
    model.component("comp1").geom("geom1").feature("uni5").selection("input").set("rt1", "wp4");
    model.component("comp1").geom("geom1").feature("uni5").label("add center flange point to chamber 2");
    model.component("comp1").geom("geom1").run("uni5");
    model.component("comp1").geom("geom1").run("uni5");
    model.component("comp1").geom("geom1").feature("mov6").selection("oldposvertex").set("uni5", 573);
    model.component("comp1").geom("geom1").run("mov6");
    model.component("comp1").geom("geom1").run("cyl4");

    model.param().set("z_c2", "0");

    model.component("comp1").geom("geom1").feature("rt1").label("rotate chamber 2");
    model.component("comp1").geom("geom1").run("rt1");
    model.component("comp1").geom("geom1").run("sel8");
    model.component("comp1").geom("geom1").run("cyl4");
    model.component("comp1").geom("geom1").feature("wp3").label("input plane chamber 1");
    model.component("comp1").geom("geom1").run("wp3");
    model.component("comp1").geom("geom1").run("wp3");
    model.component("comp1").geom("geom1").create("uni6", "Union");
    model.component("comp1").geom("geom1").feature().remove("uni6");
    model.component("comp1").geom("geom1").feature("mov6").label("Move Chamber 2 to position");
    model.component("comp1").geom("geom1").run("mov6");
    model.component("comp1").geom("geom1").feature("mov6").set("newposz", "1.1684+z_c2");
    model.component("comp1").geom("geom1").run("mov6");
    model.component("comp1").geom("geom1").run();

    model.component("comp1").physics("es").feature("gnd1").label("ground chamber 1");

    model.component("comp1").geom("geom1").run("wp1");
    model.component("comp1").geom("geom1").feature("wp1").label("mcp front face");
    model.component("comp1").geom("geom1").run("wp1");
    model.component("comp1").geom("geom1").run("mov1");
    model.component("comp1").geom("geom1").feature("imp4").active(false);
    model.component("comp1").geom("geom1").feature("imp4").active(true);
    model.component("comp1").geom("geom1").run("sel8");

    model.component("comp1").physics("es").feature("gnd1").selection().named("geom1_sel8_bnd");
    model.component("comp1").physics("es").create("gnd3", "Ground", 2);
    model.component("comp1").physics("es").feature().move("gnd3", 4);
    model.component("comp1").physics("es").feature("gnd3").label("Ground Chamber 2");
    model.component("comp1").physics("es").feature("gnd3").selection().named("geom1_sel9_bnd");
    model.component("comp1").physics("es").feature("gnd2").label("Ground needle");

    model.component("comp1").geom("geom1").feature("imp4").label("Import Chamber 1 and rails");
    model.component("comp1").geom("geom1").run("rot1");
    model.component("comp1").geom("geom1").runPre("rot1");
    model.component("comp1").geom("geom1").feature("rot1").selection("input").named("imp4");
    model.component("comp1").geom("geom1").run("rot1");
    model.component("comp1").geom("geom1").run("mov1");
    model.component("comp1").geom("geom1").run("mov1");
    model.component("comp1").geom("geom1").create("del1", "Delete");
    model.component("comp1").geom("geom1").feature("del1").label("Delete Chamber 1");
    model.component("comp1").geom("geom1").feature("del1").selection("input").init();
    model.component("comp1").geom("geom1").feature("del1").selection("input").named("sel8");
    model.component("comp1").geom("geom1").run("del1");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run();

    model.component("comp1").physics("cpt").feature("wall7").label("Chamber 1 wall");
    model.component("comp1").physics("cpt").feature("wall7").selection().named("geom1_sel8_bnd");
    model.component("comp1").physics("cpt").create("wall8", "Wall", 2);
    model.component("comp1").physics("cpt").feature("wall8").label("Chamber 2 wall");
    model.component("comp1").physics("cpt").feature("wall8").selection().named("geom1_sel9_bnd");

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();
    model.result("pg3").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg6").run();
    model.result("pg5").run();
    model.result("pg6").run();
    model.result("pg5").run();
    model.result("pg6").run();
    model.result("pg5").run();
    model.result("pg6").run();

    model.component("comp1").geom("geom1").run("sel6");

    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init(3);
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4", 1);

    model.component("comp1").geom("geom1").run("sel6");
    model.component("comp1").geom("geom1").create("wp5", "WorkPlane");
    model.component("comp1").geom("geom1").feature("wp5").set("unite", true);
    model.component("comp1").geom("geom1").feature("wp5").set("planetype", "faceparallel");
    model.component("comp1").geom("geom1").feature("wp5").selection("face").set("mov6", 455);
    model.component("comp1").geom("geom1").feature("wp5").label("side flange plane for measuring");
    model.component("comp1").geom("geom1").run("wp5");
    model.component("comp1").geom("geom1").feature("wp5").geom().create("pt1", "Point");
    model.component("comp1").geom("geom1").feature("wp5").geom().feature("pt1").label("center");
    model.component("comp1").geom("geom1").feature("wp5").geom().run("pt1");
    model.component("comp1").geom("geom1").measure().selection().init(2);
    model.component("comp1").geom("geom1").measure().selection().set("mov6", 455);
    model.component("comp1").geom("geom1").run("wp5");
    model.component("comp1").geom("geom1").measure().selection().init(2);
    model.component("comp1").geom("geom1").measure().selection()
         .all(new String[]{"mov6(1)", "cyl4(1)", "mov1(2)", "mov1(3)", "mov1(4)", "mov1(5)", "mov1(6)", "mov1(7)", "mov1(8)", "mov1(9)", 
         "mov1(10)", "mov1(11)", "mov1(12)", "mov1(13)", "mov1(14)", "mov1(15)", "mov1(16)", "mov1(17)", "mov1(18)", "mov2(1)", 
         "mov2(2)", "mov2(3)", "mov2(4)", "mov5(1)", "mov5(2)", "mov5(4)", "dif8(1)", "arr4(1,1,1)", "arr4(2,1,1)", "arr4(1,2,1)", 
         "arr4(2,2,1)", "dif9(1)", "cyl23(1)", "wp5.pt1"});
    model.component("comp1").geom("geom1").measure().selection().init(0);
    model.component("comp1").geom("geom1").measure().selection().set("wp5", 1);

    model.param().set("z_c2_center", "215.9[mm]");

    model.component("comp1").geom("geom1").feature("del1").active(false);
    model.component("comp1").geom("geom1").feature("imp7").active(false);
    model.component("comp1").geom("geom1").run("uni4");
    model.component("comp1").geom("geom1").run("rt1");
    model.component("comp1").geom("geom1").feature("wp4").active(false);
    model.component("comp1").geom("geom1").run("uni5");
    model.component("comp1").geom("geom1").feature("mov6").active(false);
    model.component("comp1").geom("geom1").run("sel6");
    model.component("comp1").geom("geom1").feature().move("wp5", 7);
    model.component("comp1").geom("geom1").run("mov6");
    model.component("comp1").geom("geom1").feature("wp5").active(false);
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").measure().selection().init(2);
    model.component("comp1").geom("geom1").measure().selection()
         .all(new String[]{"uni5(1)", "cyl4(1)", "mov1(1)", "mov1(2)", "mov1(3)", "mov1(4)", "mov1(5)", "mov1(6)", "mov1(7)", "mov1(8)", 
         "mov1(9)", "mov1(10)", "mov1(11)", "mov1(12)", "mov1(13)", "mov1(14)", "mov1(15)", "mov1(16)", "mov1(17)", "mov1(18)", 
         "mov2(1)", "mov2(2)", "mov2(3)", "mov2(4)", "mov5(1)", "mov5(2)", "mov5(4)", "dif8(1)", "arr4(1,1,1)", "arr4(2,1,1)", 
         "arr4(1,2,1)", "arr4(2,2,1)", "dif9(1)", "cyl23(1)"});
    model.component("comp1").geom("geom1").measure().selection().init(2);
    model.component("comp1").geom("geom1").measure().selection().set("mov1(1)", 1, 76);
    model.component("comp1").geom("geom1").measure().selection().init(2);
    model.component("comp1").geom("geom1").measure().selection().set("mov1(1)", 1, 76);
    model.component("comp1").geom("geom1").measure().selection().init(0);
    model.component("comp1").geom("geom1").measure().selection().set("mov1(1)", 1, 113);

    model.param().set("L_c1", "300[mm]");
    model.param().set("z_c2", "if(cfg==3,L_c1,0[mm])");
    model.param().set("mcp_z", "if(cfg==1,z_mcp_c1, if(cfg==2, z_c2_center, z_c2_center+L_c1))");
    model.param().set("z_mcp_1", "250[mm]");
    model.param().rename("z_mcp_1", "z_mcp_c1");

    model.sol("sol1").study("std1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").attach("std1");

    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.sol("sol1").study("std1");
    model.sol("sol1").attach("std1");

    model.component("comp1").geom("geom1").run("del1");
    model.component("comp1").geom("geom1").run("del1");
    model.component("comp1").geom("geom1").run("mov1");

    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4");
    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").run("cyl23");

    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4");

    model.component("comp1").geom("geom1").run("cyl23");
    model.component("comp1").geom("geom1").create("uni6", "Union");
    model.component("comp1").geom("geom1").feature("uni6").selection("input").set("mov1(1)");
    model.component("comp1").geom("geom1").feature("uni6").selection("input").init();
    model.component("comp1").geom("geom1").feature().remove("uni6");
    model.component("comp1").geom("geom1").run("uni4");
    model.component("comp1").geom("geom1").run("sel9");
    model.component("comp1").geom("geom1").run("uni5");
    model.component("comp1").geom("geom1").feature("uni4").active(false);
    model.component("comp1").geom("geom1").run("sel9");
    model.component("comp1").geom("geom1").feature("rt1").active(false);

    model.param().set("cfg", "1");

    model.component("comp1").geom("geom1").run("wp4");
    model.component("comp1").geom("geom1").feature("uni5").active(false);
    model.component("comp1").geom("geom1").run("sel8");
    model.component("comp1").geom("geom1").runPre("fin");

    model.sol("sol1").study("std1");
    model.sol("sol1").attach("std1");

    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").run("mov1");
    model.component("comp1").geom("geom1").run("mov1");
    model.component("comp1").geom("geom1").create("sel10", "ExplicitSelection");
    model.component("comp1").geom("geom1").feature("sel10").selection("selection").init(2);
    model.component("comp1").geom("geom1").feature("sel10").selection("selection")
         .set("mov1(1)", 33, 34, 35, 36, 37, 38, 40);
    model.component("comp1").geom("geom1").feature("sel10").label("meshing issue flange");
    model.component("comp1").geom("geom1").run("sel10");
    model.component("comp1").geom("geom1").run("sel10");
    model.component("comp1").geom("geom1").create("del2", "Delete");
    model.component("comp1").geom("geom1").feature("del2").label("Delete flange w/ meshing issue");
    model.component("comp1").geom("geom1").feature("del2").selection("input").named("sel10");
    model.component("comp1").geom("geom1").run("del2");
    model.component("comp1").geom("geom1").runPre("sel10");
    model.component("comp1").geom("geom1").feature("sel10").selection("selection")
         .set("mov1(1)", 33, 34, 35, 36, 37, 38, 39, 40);
    model.component("comp1").geom("geom1").run("sel10");
    model.component("comp1").geom("geom1").run("del2");
    model.component("comp1").geom("geom1").runPre("fin");

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").run();

    model.label("lens8newMCP_screencross7_ks_v2_multi_flange_config.mph");

    model.result("pg1").run();

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});

    return model;
  }

  public static Model run17(Model model) {
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").run();
    model.result("pg1").run();

    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").run("fin");

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.param().set("cfg", "2");

    model.component("comp1").geom("geom1").run("sel6");
    model.component("comp1").geom("geom1").create("if1", "If");
    model.component("comp1").geom("geom1").feature().createAfter("endif1", "EndIf", "if1");
    model.component("comp1").geom("geom1").feature().move("if1", 0);
    model.component("comp1").geom("geom1").feature().move("endif1", 1);
    model.component("comp1").geom("geom1").feature().move("endif1", 8);
    model.component("comp1").geom("geom1").feature("if1").label("If need spherical chamber 2");
    model.component("comp1").geom("geom1").feature("if1").set("condition", "cfg==2||cfg==3");
    model.component("comp1").geom("geom1").run("if1");
    model.component("comp1").geom("geom1").feature("imp7").active(true);
    model.component("comp1").geom("geom1").feature("uni4").active(true);
    model.component("comp1").geom("geom1").feature("rt1").active(true);
    model.component("comp1").geom("geom1").feature("uni5").active(true);
    model.component("comp1").geom("geom1").feature("wp4").active(true);
    model.component("comp1").geom("geom1").feature("mov6").active(true);
    model.component("comp1").geom("geom1").feature("endif1").label("End spherical chamber");
    model.component("comp1").geom("geom1").run("if1");
    model.component("comp1").geom("geom1").feature().move("endif1", 9);
    model.component("comp1").geom("geom1").feature("wp5").active(true);
    model.component("comp1").geom("geom1").run("if1");
    model.component("comp1").geom("geom1").create("if2", "If");
    model.component("comp1").geom("geom1").feature().createAfter("endif2", "EndIf", "if2");
    model.component("comp1").geom("geom1").feature().move("endif2", 12);
    model.component("comp1").geom("geom1").feature().move("if2", 11);
    model.component("comp1").geom("geom1").feature().move("endif2", 19);
    model.component("comp1").geom("geom1").feature().remove("del1");
    model.component("comp1").geom("geom1").feature("if2").label("If tube chamber");
    model.component("comp1").geom("geom1").feature("if2").set("condition", "cfg==1||cfg==3");
    model.component("comp1").geom("geom1").run("rt1");

    model.param().set("cfg", "1");

    model.component("comp1").geom("geom1").run("if1");
    model.component("comp1").geom("geom1").runPre("fin");

    model.param().set("cfg", "2");

    model.component("comp1").geom("geom1").run("rt1");
    model.component("comp1").geom("geom1").feature("wp4").selection("face").set("rt1", 334);
    model.component("comp1").geom("geom1").run("wp4");
    model.component("comp1").geom("geom1").run("uni5");
    model.component("comp1").geom("geom1").feature("mov6").selection("oldposvertex").set("uni5", 699);
    model.component("comp1").geom("geom1").run("mov6");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("rt1");
    model.component("comp1").geom("geom1").run("rt1");
    model.component("comp1").geom("geom1").feature("wp4").selection("face").clear("rt1");
    model.component("comp1").geom("geom1").feature("wp4").selection("face").set("rt1", 870);
    model.component("comp1").geom("geom1").run("wp4");
    model.component("comp1").geom("geom1").run("mov6");
    model.component("comp1").geom("geom1").runPre("fin");

    model.label("lens8newMCP_screencross7_ks_v2_multi_flange_config.mph");

    model.result("pg1").run();

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.component("comp1").view("view1").set("showgrid", true);

    model.sol("sol2").runAll();

    model.label("lens8newMCP_screencross7_ks_v2_multi_flange_config.mph");

    model.component("comp1").view("view1").camera().set("projection", "orthographic");

    model.result("pg3").run();

    model.component("comp1").view("view1").camera().set("projection", "perspective");

    model.result("pg1").run();

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();
    model.result("pg3").run();
    model.result("pg1").run();

    model.sol("sol2").runAll();

    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").active(false);

    model.component("comp1").geom("geom1").run("fin");

    model.result("pg1").run();
    model.result("pg3").run();

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.param().set("cfg", "1");

    model.component("comp1").geom("geom1").run("if2");

    model.param().set("cfg", "2");

    model.component("comp1").geom("geom1").run("fin");

    model.result("pg1").run();
    model.result("pg5").run();

    model.component("comp1").physics("cpt").feature("pbeam1").set("N", 10000);

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg5").run();
    model.result().dataset("cpl1").set("quickz", "tip_z+1[mm]");
    model.result("pg5").run();
    model.result().dataset("cpl2").set("quickz", "mcp_z-1[mm]");
    model.result("pg6").run();
    model.result("pg5").run();
    model.result("pg6").run();
    model.result("pg5").run();
    model.result("pg6").run();
    model.result("pg5").run();
    model.result("pg6").run();

    model.component("comp1").geom("geom1").feature("imp4")
         .set("filename", "C:\\Users\\eiko\\OneDrive - California Institute of Technology\\college files (onedrive)\\Roukes lab research\\comsol_stuff\\tube chamber.step");

    model.param().set("cfg", "1");

    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").run("sel8");
    model.component("comp1").geom("geom1").run("sel8");

    model.component("comp1").view("view1").hideObjects().create("hide2");
    model.component("comp1").view("view1").hideObjects("hide2").init();
    model.component("comp1").view("view1").hideObjects("hide2").add("cyl4");

    model.component("comp1").geom("geom1").feature("sel8").selection("selection").set("imp4");
    model.component("comp1").geom("geom1").run("sel8");
    model.component("comp1").geom("geom1").run("sel10");
    model.component("comp1").geom("geom1").feature("sel10").selection("selection").init();
    model.component("comp1").geom("geom1").feature("sel10").selection("selection").init(2);
    model.component("comp1").geom("geom1").feature("sel10").selection("selection")
         .set("mov1(1)", 61, 62, 64, 65, 66, 67, 72);
    model.component("comp1").geom("geom1").run("sel10");
    model.component("comp1").geom("geom1").run("del2");
    model.component("comp1").geom("geom1").runPre("sel10");
    model.component("comp1").geom("geom1").feature("sel10").selection("selection")
         .set("mov1(1)", 61, 62, 63, 64, 65, 66, 67, 72);
    model.component("comp1").geom("geom1").run("sel10");
    model.component("comp1").geom("geom1").run("del2");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("imp4");
    model.component("comp1").geom("geom1").run("rot1");
    model.component("comp1").geom("geom1").feature("rot1").active(false);
    model.component("comp1").geom("geom1").run("sel10");
    model.component("comp1").geom("geom1").runPre("wp3");
    model.component("comp1").geom("geom1").feature("wp3").selection("face").clear("imp4");
    model.component("comp1").geom("geom1").feature("wp3").selection("face").set("imp4", 19);
    model.component("comp1").geom("geom1").run("wp3");
    model.component("comp1").geom("geom1").run("mov1");
    model.component("comp1").geom("geom1").runPre("fin");

    model.param().set("cfg", "2");

    model.component("comp1").geom("geom1").run("fin");

    model.param().set("cfg", "1");

    model.component("comp1").geom("geom1").run("fin");

    model.param().set("cfg", "3");

    model.component("comp1").geom("geom1").run("fin");

    model.param().set("L_dom", "if(cfg==3,2*z_c2+L_c1,L_c1)");

    model.component("comp1").geom("geom1").run("sel9");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("sel4");

    model.component("comp1").view("view1").hideObjects().clear();

    model.component("comp1").geom("geom1").run("dif2");
    model.component("comp1").geom("geom1").feature("cyl4").set("h", "L_dom");
    model.component("comp1").geom("geom1").run("cyl4");
    model.component("comp1").geom("geom1").runPre("fin");

    model.label("lens8newMCP_screencross7_ks_v2_multi_flange_config.mph");

    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init();
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4");

    model.component("comp1").geom("geom1").measure().selection().init();
    model.component("comp1").geom("geom1").measure().selection()
         .set("mov6(1)", "wp5.pt1", "cyl4(1)", "mov1(2)", "del2(1)", "mov2(1)", "mov2(2)", "mov2(3)", "mov2(4)", "mov5(1)", "mov5(2)", "mov5(4)", "dif8(1)", "arr4(1,1,1)", "arr4(2,1,1)", "arr4(1,2,1)", "arr4(2,2,1)", "dif9(1)", "cyl23(1)");
    model.component("comp1").geom("geom1").measure().selection().init(0);
    model.component("comp1").geom("geom1").measure().selection().set("del2", 99, 102);
    model.component("comp1").geom("geom1").measure().selection().init(0);
    model.component("comp1").geom("geom1").measure().selection().set("del2", 99, 102);
    model.component("comp1").geom("geom1").measure().selection().init(0);
    model.component("comp1").geom("geom1").measure().selection().set("mov6", 1014);
    model.component("comp1").geom("geom1").measure().selection().set("del2", 99, 102);
    model.component("comp1").geom("geom1").measure().selection().init(0);
    model.component("comp1").geom("geom1").measure().selection().set("mov6", 1014, 1017);
    model.component("comp1").geom("geom1").measure().selection().set("del2", 99, 102);
    model.component("comp1").geom("geom1").measure().selection().init(0);
    model.component("comp1").geom("geom1").measure().selection().set("mov6", 1014, 1017);
    model.component("comp1").geom("geom1").measure().selection().set("del2", 99, 102);
    model.component("comp1").geom("geom1").measure().selection().init(0);
    model.component("comp1").geom("geom1").measure().selection().set("mov6", 956, 1017);
    model.component("comp1").geom("geom1").measure().selection().set("del2", 99, 102);
    model.component("comp1").geom("geom1").measure().selection().init(0);
    model.component("comp1").geom("geom1").measure().selection().set("mov6", 956, 1007, 1016, 1017);
    model.component("comp1").geom("geom1").measure().selection().set("del2", 99, 102);

    model.param().set("L_dom", "if(cfg==3,2*z_c2_center+L_c1,L_c1)");

    model.component("comp1").geom("geom1").run("fin");

    model.component("comp1").view("view1").hideObjects().clear();

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");

    model.component("comp1").geom("geom1").measure().selection().init(0);
    model.component("comp1").geom("geom1").measure().selection().set("fin", 964);
    model.component("comp1").geom("geom1").measure().selection().init(0);
    model.component("comp1").geom("geom1").measure().selection().set("fin", 748, 964);
    model.component("comp1").geom("geom1").measure().selection().init(0);
    model.component("comp1").geom("geom1").measure().selection().set("fin", 748, 963, 964);
    model.component("comp1").geom("geom1").measure().selection().init(0);
    model.component("comp1").geom("geom1").measure().selection().set("fin", 748, 963, 964, 1177);
    model.component("comp1").geom("geom1").measure().selection().init(0);
    model.component("comp1").geom("geom1").measure().selection().set("fin", 748, 963, 1177);
    model.component("comp1").geom("geom1").measure().selection().init(0);
    model.component("comp1").geom("geom1").measure().selection().set("fin", 748, 963, 965, 1177);
    model.component("comp1").geom("geom1").measure().selection().init(0);
    model.component("comp1").geom("geom1").measure().selection().set("fin", 748, 965);
    model.component("comp1").geom("geom1").measure().selection().init(0);
    model.component("comp1").geom("geom1").measure().selection().set("fin", 965);

    model.param().set("cfg", "2");

    model.component("comp1").geom("geom1").run("fin");

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.param().set("cfg", "3");

    model.component("comp1").geom("geom1").run("fin");

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");

    model.component("comp1").geom("geom1").run("sel6");
    model.component("comp1").geom("geom1").create("sph1", "Sphere");
    model.component("comp1").geom("geom1").feature("sph1").set("pos", new double[]{0, 0.5, 87});
    model.component("comp1").geom("geom1").feature("sph1").set("r", 2);
    model.component("comp1").geom("geom1").run("sph1");

    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init(3);
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4", 1);

    model.component("comp1").geom("geom1").run("sph1");
    model.component("comp1").geom("geom1").feature("sph1").set("r", 100);
    model.component("comp1").geom("geom1").run("sph1");
    model.component("comp1").geom("geom1").feature("sph1").set("r", 10);
    model.component("comp1").geom("geom1").run("sph1");
    model.component("comp1").geom("geom1").feature("sph1").active(false);

    model.param().set("cfg", "1");

    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").run("imp4");
    model.component("comp1").geom("geom1").run("wp3");
    model.component("comp1").geom("geom1").run("mov1");

    return model;
  }

  public static Model run18(Model model) {
    model.component("comp1").geom("geom1").run("sel10");
    model.component("comp1").geom("geom1").run("cone1");
    model.component("comp1").geom("geom1").runPre("fin");

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.label("lens8newMCP_screencross7_ks_v2_multi_flange_config.mph");

    model.result("pg1").run();

    model.component("comp1").view("view1").hideObjects("hide1").active(false);
    model.component("comp1").view("view1").hideObjects().remove("hide1");

    model.component("comp1").geom("geom1").run("fin");

    model.sol("sol1").study("std1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").attach("std1");

    model.param().set("L_dom", "if(cfg==3,2*z_c2_center+L_c1+0.1[m],L_c1+0.1[m])");

    model.component("comp1").geom("geom1").run("fin");

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.param().set("cfg", "3");

    model.component("comp1").geom("geom1").run("fin");

    model.sol("sol1").study("std1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").attach("std1");

    model.component("comp1").geom("geom1").feature("imp7").set("keepbnd", false);
    model.component("comp1").geom("geom1").run("imp7");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run();

    model.sol("sol1").study("std1");
    model.sol("sol1").attach("std1");

    model.component("comp1").geom("geom1").feature("imp7").set("keepbnd", true);
    model.component("comp1").geom("geom1").feature("imp7").set("fillholes", true);
    model.component("comp1").geom("geom1").run("imp7");
    model.component("comp1").geom("geom1").runPre("fin");

    model.sol("sol1").study("std1");
    model.sol("sol1").attach("std1");

    model.component("comp1").geom("geom1").runPre("uni4");
    model.component("comp1").geom("geom1").feature("uni4").selection("input")
         .set("imp7.Port_A_Flange1", "imp7.Port_B_Flange1", "imp7.Port_C_Flange1", "imp7.Port_D_Flange1", "imp7.Port_E_Flange1", "imp7.Port_F_Flange1", "imp7.Port_G_Flange1", "imp7.Port_H_Flange1", "imp7.Port_I_Flange1", "imp7.Port_J_Flange1", "imp7.Port_L_Flange1", "imp7.Port_M_Flange1", "imp7.Port_N_Flange1", "imp7.Port_O_Flange1", "imp7.Port_P_Flange1", "imp7.Sphere1");
    model.component("comp1").geom("geom1").run("uni4");
    model.component("comp1").geom("geom1").run("uni4");
    model.component("comp1").geom("geom1").create("del3", "Delete");
    model.component("comp1").geom("geom1").run("uni4");
    model.component("comp1").geom("geom1").feature("del3").active(false);

    model.param().set("cfg", "1");

    model.component("comp1").geom("geom1").run("fin");

    model.param().set("cfg", "2");

    model.component("comp1").geom("geom1").run("fin");

    model.param().set("cfg", "3");

    model.component("comp1").geom("geom1").run("fin");

    model.param().set("cfg", "2");

    model.component("comp1").geom("geom1").run("fin");

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg5").run();
    model.result("pg6").run();
    model.result("pg5").run();
    model.result("pg3").run();
    model.result("pg5").run();

    model.component("comp1").view("view1").camera().set("projection", "orthographic");

    model.param().set("cfg", "3");

    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").run("sph1");
    model.component("comp1").geom("geom1").create("if3", "If");
    model.component("comp1").geom("geom1").feature().createAfter("endif3", "EndIf", "if3");
    model.component("comp1").geom("geom1").feature().move("if3", 3);
    model.component("comp1").geom("geom1").feature().move("endif3", 5);
    model.component("comp1").geom("geom1").feature("del3").active(true);
    model.component("comp1").geom("geom1").run("uni4");
    model.component("comp1").geom("geom1").runPre("del3");
    model.component("comp1").geom("geom1").feature("del3").selection("input").init();
    model.component("comp1").geom("geom1").feature("del3").selection("input").set("imp7.Port_K_Flange1");
    model.component("comp1").geom("geom1").feature("if3").set("condition", "cfg==3");
    model.component("comp1").geom("geom1").runPre("fin");

    model.component("comp1").mesh("mesh1").run("size");

    model.sol("sol1").study("std1");
    model.sol("sol1").feature().remove("st1");
    model.sol("sol1").feature().remove("v1");
    model.sol("sol1").feature().remove("s1");
    model.sol("sol1").attach("std1");

    model.component("comp1").geom("geom1").run("if3");
    model.component("comp1").geom("geom1").run("sel9");
    model.component("comp1").geom("geom1").run("rt1");
    model.component("comp1").geom("geom1").run("del3");
    model.component("comp1").geom("geom1").runPre("uni4");
    model.component("comp1").geom("geom1").feature("uni4").selection("input").set("imp7");
    model.component("comp1").geom("geom1").run("uni4");
    model.component("comp1").geom("geom1").run("del3");
    model.component("comp1").geom("geom1").runPre("del3");
    model.component("comp1").geom("geom1").feature("del3").selection("input").init();
    model.component("comp1").geom("geom1").runPre("uni4");
    model.component("comp1").geom("geom1").feature("uni4").selection("input")
         .set("imp7.Port_A_Flange1", "imp7.Port_B_Flange1", "imp7.Port_C_Flange1", "imp7.Port_D_Flange1", "imp7.Port_E_Flange1", "imp7.Port_G_Flange1", "imp7.Port_H_Flange1", "imp7.Port_I_Flange1", "imp7.Port_J_Flange1", "imp7.Port_K_Flange1", "imp7.Port_L_Flange1", "imp7.Port_M_Flange1", "imp7.Port_N_Flange1", "imp7.Port_O_Flange1", "imp7.Port_P_Flange1", "imp7.Sphere1");
    model.component("comp1").geom("geom1").run("uni4");
    model.component("comp1").geom("geom1").run("if3");
    model.component("comp1").geom("geom1").feature("del3").selection("input").set("imp7.Port_F_Flange1");
    model.component("comp1").geom("geom1").run("del3");
    model.component("comp1").geom("geom1").runPre("fin");

    model.sol("sol1").study("std1");
    model.sol("sol1").attach("std1");

    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size2").selection().named("geom1_sel9_dom");
    model.component("comp1").mesh("mesh1").feature("ftet4").create("size4", "Size");
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size4").selection().geom("geom1", 3);
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size4").selection().named("geom1_sel8_dom");
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size4").selection()
         .named("geom1_imp4_Body1_dom");
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size4").selection().named("geom1_sel8_dom");

    model.component("comp1").geom("geom1").run("fin");
    model.component("comp1").geom("geom1").run("fin");

    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size4").selection()
         .named("geom1_imp4_Body1_dom");
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size4").selection().named("geom1_sel8_dom");

    model.component("comp1").geom("geom1").run("sel8");
    model.component("comp1").geom("geom1").run("sel8");
    model.component("comp1").geom("geom1").run("mov1");
    model.component("comp1").geom("geom1").run("imp4");
    model.component("comp1").geom("geom1").run("if2");
    model.component("comp1").geom("geom1").run("imp4");
    model.component("comp1").geom("geom1").run("sel8");
    model.component("comp1").geom("geom1").run("sel10");
    model.component("comp1").geom("geom1").run("sel8");
    model.component("comp1").geom("geom1").feature("sel8").set("contributeto", "none");
    model.component("comp1").geom("geom1").run("sel8");
    model.component("comp1").geom("geom1").run("del2");
    model.component("comp1").geom("geom1").runPre("fin");

    model.component("comp1").physics("es").create("fcal1", "ForceCalculation", 3);
    model.component("comp1").physics("es").feature("fcal1").selection().named("geom1_sel8_dom");

    model.component("comp1").geom("geom1").selection().create("csel2", "CumulativeSelection");
    model.component("comp1").geom("geom1").selection("csel2").label("Cumulative Selection 2a");
    model.component("comp1").geom("geom1").feature("sel8").set("contributeto", "csel2");
    model.component("comp1").geom("geom1").runPre("fin");

    model.component("comp1").physics("es").feature("fcal1").selection().named("geom1_csel2_dom");

    model.component("comp1").geom("geom1").runPre("sel8");
    model.component("comp1").geom("geom1").feature("sel8").set("selshow", "dom");
    model.component("comp1").geom("geom1").runPre("fin");

    model.component("comp1").physics("es").feature("fcal1").selection().named("geom1_imp7_dom");
    model.component("comp1").physics("es").feature("fcal1").selection().named("geom1_csel2_dom");
    model.component("comp1").physics("es").feature("fcal1").selection().named("geom1_sel9_dom");
    model.component("comp1").physics("es").feature("fcal1").selection().named("geom1_csel2_dom");
    model.component("comp1").physics("es").feature("fcal1").selection().named("geom1_sel8_dom");

    model.component("comp1").geom("geom1").feature("imp4").set("contributeto", "none");
    model.component("comp1").geom("geom1").selection().create("csel3", "CumulativeSelection");
    model.component("comp1").geom("geom1").selection("csel3").label("Cumulative Selection 3");
    model.component("comp1").geom("geom1").feature("imp4").set("contributeto", "csel3");
    model.component("comp1").geom("geom1").runPre("fin");

    model.component("comp1").physics("es").feature("fcal1").selection().named("geom1_csel3_dom");

    model.component("comp1").geom("geom1").feature("mov1").set("selresult", true);
    model.component("comp1").geom("geom1").selection().create("csel4", "CumulativeSelection");
    model.component("comp1").geom("geom1").selection("csel4").label("Cumulative Selection 4");
    model.component("comp1").geom("geom1").feature("mov1").set("contributeto", "csel4");
    model.component("comp1").geom("geom1").runPre("fin");

    model.component("comp1").physics("es").feature("fcal1").selection().named("geom1_csel4_dom");

    model.component("comp1").selection().create("sel7", "Explicit");

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);
    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();
    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);
    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.component("comp1").geom("geom1").run("imp4");
    model.component("comp1").geom("geom1").run("wp3");
    model.component("comp1").geom("geom1").run("cyl4");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").runPre("rot1");
    model.component("comp1").geom("geom1").feature("rot1").selection("input").init();
    model.component("comp1").geom("geom1").feature("rot1").selection("input").named("csel3");
    model.component("comp1").geom("geom1").feature("rot1").selection("input").named("csel4");
    model.component("comp1").geom("geom1").feature("rot1").selection("input").named("csel3");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").runPre("mov1");
    model.component("comp1").geom("geom1").feature("mov1").set("contributeto", "csel3");
    model.component("comp1").geom("geom1").selection().create("csel5", "CumulativeSelection");
    model.component("comp1").geom("geom1").selection("csel5").label("Cumulative Selection 5");
    model.component("comp1").geom("geom1").feature("mov1").set("contributeto", "csel5");
    model.component("comp1").geom("geom1").runPre("fin");

    model.component("comp1").physics("es").feature("fcal1").selection().named("geom1_csel5_dom");
    model.component("comp1").physics("es").feature("fcal1").selection().named("geom1_imp4_dom");
    model.component("comp1").physics("es").feature("fcal1").selection().named("geom1_sel6");
    model.component("comp1").physics("es").feature("fcal1").selection().named("geom1_csel5_dom");

    model.component("comp1").geom("geom1").feature("mov1").set("selresultshow", "all");
    model.component("comp1").geom("geom1").feature("mov1").set("contributeto", "csel5");
    model.component("comp1").geom("geom1").runPre("fin");

    model.component("comp1").view("view1").hideEntities().create("hide1");
    model.component("comp1").view("view1").hideEntities("hide1").geom(3);
    model.component("comp1").view("view1").hideEntities("hide1").add(2);
    model.component("comp1").view("view1").hideObjects().clear();
    model.component("comp1").view("view1").hideEntities().clear();
    model.component("comp1").view("view1").hideMesh().clear();

    model.component("comp1").selection("sel7").all();
    model.component("comp1").selection("sel7").geom("geom1", 3);
    model.component("comp1").selection("sel7")
         .set(23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44);

    model.component("comp1").geom("geom1").feature("imp4").set("selresultshow", "all");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").run("imp4");

    model.component("comp1").view("view1").hideObjects().create("hide1");
    model.component("comp1").view("view1").hideObjects("hide1").init(2);
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4", 6);
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4", 3);
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4", 5);
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4", 1);
    model.component("comp1").view("view1").hideObjects("hide1").add("cyl4", 2);

    model.component("comp1").geom("geom1").feature("imp4").set("selresultshow", "dom");
    model.component("comp1").geom("geom1").run("imp4");
    model.component("comp1").geom("geom1").feature("sel8").selection("selection").init(3);
    model.component("comp1").geom("geom1").feature("sel8").selection("selection").set("imp4", 1);
    model.component("comp1").geom("geom1").runPre("fin");

    model.component("comp1").physics("es").feature("fcal1").selection().named("geom1_csel2_dom");

    model.component("comp1").geom("geom1").runPre("mov1");
    model.component("comp1").geom("geom1").feature("mov1").set("contributeto", "csel4");
    model.component("comp1").geom("geom1").runPre("fin");

    model.component("comp1").physics("es").feature("fcal1").selection().named("geom1_csel4_dom");

    model.component("comp1").selection("sel7").all();
    model.component("comp1").selection("sel7").set(2);

    model.component("comp1").geom("geom1").feature().move("cyl4", 70);
    model.component("comp1").geom("geom1").run("cyl4");
    model.component("comp1").geom("geom1").runPre("fin");

    model.component("comp1").view("view1").hideObjects().clear();

    model.component("comp1").geom("geom1").run();

    model.component("comp1").selection("sel7").set();

    model.component("comp1").geom("geom1").run("cyl4");
    model.component("comp1").geom("geom1").feature("cyl4").set("type", "solid");

    model.component("comp1").selection().remove("sel7");

    model.component("comp1").physics("es").feature("fcal1").selection().named("geom1_sel8");

    model.component("comp1").geom("geom1").run("sph1");
    model.component("comp1").geom("geom1").run("sph1");
    model.component("comp1").geom("geom1").run("cyl4");
    model.component("comp1").geom("geom1").run("fin");

    model.component("comp1").physics("es").feature().remove("fcal1");
    model.component("comp1").physics("es").feature("gnd1").selection().named("geom1_mov1_bnd");

    model.component("comp1").geom("geom1").runPre("fin");

    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size4").selection().named("geom1_mov1_dom");
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size4").selection().named("geom1_imp4_dom");

    model.component("comp1").geom("geom1").run("if2");
    model.component("comp1").geom("geom1").run("imp4");
    model.component("comp1").geom("geom1").run("sel8");
    model.component("comp1").geom("geom1").run("wp3");
    model.component("comp1").geom("geom1").run("wp3");
    model.component("comp1").geom("geom1").run("sel10");
    model.component("comp1").geom("geom1").runPre("fin");
    model.component("comp1").geom("geom1").runPre("fin");

    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size4").selection().named("geom1_sel8");
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size2").selection().named("geom1_imp4_dom");
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size2").selection().named("geom1_sel9_dom");
    model.component("comp1").mesh("mesh1").feature("ftet4").feature().remove("size4");
    model.component("comp1").mesh("mesh1").feature("ftet4").create("size4", "Size");
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size4").selection().geom("geom1", 3);
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size4").selection().named("geom1_csel1_dom");
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size4").selection()
         .named("geom1_imp4_Body1_dom");
    model.component("comp1").mesh("mesh1").feature("ftet4").feature().move("size4", 0);
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size4").selection().named("geom1_sel8");
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size4").selection().named("geom1_imp4_dom");

    model.component("comp1").geom("geom1").run("sel9");
    model.component("comp1").geom("geom1").run("sel8");
    model.component("comp1").geom("geom1").feature("sel8").selection("selection").init();
    model.component("comp1").geom("geom1").feature("sel8").selection("selection").set("imp4");
    model.component("comp1").geom("geom1").run("sel8");
    model.component("comp1").geom("geom1").run("wp3");
    model.component("comp1").geom("geom1").runPre("fin");

    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size4").selection().named("geom1_sel8_dom");
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size4").selection().geom("geom1");
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size4").selection().named("geom1_sel8_dom");
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size4").selection().named("geom1_imp4_dom");
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size4").selection()
         .named("geom1_imp4_Body1_dom");
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size4").selection().named("geom1_sel8_dom");
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size4").selection().named("geom1_rot1_dom");
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size4").selection().named("geom1_sel8_dom");
    model.component("comp1").mesh("mesh1").feature("ftet4").feature().move("size4", 3);

    model.component("comp1").physics("es").create("gnd4", "Ground", 2);
    model.component("comp1").physics("es").feature("gnd4").selection().named("geom1_mov1_bnd");
    model.component("comp1").physics("es").feature("gnd4").selection().named("geom1_sel8_bnd");

    model.component("comp1").geom("geom1").run("sel8");
    model.component("comp1").geom("geom1").runPre("fin");

    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size4").selection().geom("geom1");
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size4").selection().geom("geom1", 1);
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size4").selection().named("geom1_sel8_edg");
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size4").selection().geom("geom1", 2);
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size4").selection().named("geom1_sel8_bnd");
    model.component("comp1").mesh("mesh1").feature("ftet4").feature("size4").set("hauto", 3);
    model.component("comp1").mesh("mesh1").run("ftet4");

    model.sol("sol1").study("std1");

    model.study("std1").feature("stat").set("notlistsolnum", 1);
    model.study("std1").feature("stat").set("notsolnum", "1");
    model.study("std1").feature("stat").set("listsolnum", 1);
    model.study("std1").feature("stat").set("solnum", "1");

    model.sol("sol1").create("st1", "StudyStep");
    model.sol("sol1").feature("st1").set("study", "std1");
    model.sol("sol1").feature("st1").set("studystep", "stat");
    model.sol("sol1").create("v1", "Variables");
    model.sol("sol1").feature("v1").set("control", "stat");
    model.sol("sol1").create("s1", "Stationary");
    model.sol("sol1").feature("s1").create("fc1", "FullyCoupled");
    model.sol("sol1").feature("s1").create("i1", "Iterative");
    model.sol("sol1").feature("s1").feature("i1").set("linsolver", "cg");
    model.sol("sol1").feature("s1").feature("i1").create("mg1", "Multigrid");
    model.sol("sol1").feature("s1").feature("i1").feature("mg1").set("prefun", "amg");
    model.sol("sol1").feature("s1").feature("fc1").set("linsolver", "i1");
    model.sol("sol1").feature("s1").feature().remove("fcDef");
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notsolvertype", "solnum");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("notlistsolnum", new String[]{"1"});
    model.sol("sol2").feature("v1").set("notsolnum", "auto");
    model.sol("sol2").feature("v1").set("control", "time");

    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolvertype", "solnum");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notlistsolnum", new String[]{"1"});
    model.study("std2").feature("time").set("notsolnum", "auto");
    model.study("std2").feature("time").set("notsolnumhide", "off");
    model.study("std2").feature("time").set("notstudyhide", "on");
    model.study("std2").feature("time").set("notsolhide", "on");

    model.sol("sol1").attach("std1");
    model.sol("sol1").runAll();

    model.result("pg1").run();

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.study("std2").feature("time").set("tlist", "range(0,1e-7,3e-4)");

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 2007, 0);
    model.result("pg3").run();

    model.label("lens8newMCP_screencross7_ks_v2_multi_flange_config.mph");

    model.result("pg3").run();
    model.result().export().create("anim1", "Animation");
    model.result().export("anim1").set("target", "player");
    model.result().export("anim1").set("fontsize", "9");
    model.result().export("anim1").set("customcolor", new double[]{1, 1, 1});
    model.result().export("anim1").set("background", "color");
    model.result().export("anim1").set("gltfincludelines", "on");
    model.result().export("anim1").set("title1d", "on");
    model.result().export("anim1").set("legend1d", "on");
    model.result().export("anim1").set("logo1d", "on");
    model.result().export("anim1").set("options1d", "on");
    model.result().export("anim1").set("title2d", "on");
    model.result().export("anim1").set("legend2d", "on");
    model.result().export("anim1").set("logo2d", "on");
    model.result().export("anim1").set("options2d", "on");
    model.result().export("anim1").set("title3d", "on");
    model.result().export("anim1").set("legend3d", "on");
    model.result().export("anim1").set("logo3d", "on");

    return model;
  }

  public static Model run19(Model model) {
    model.result().export("anim1").set("options3d", "on");
    model.result().export("anim1").set("axisorientation", "on");
    model.result().export("anim1").set("grid", "on");
    model.result().export("anim1").set("axes1d", "on");
    model.result().export("anim1").set("axes2d", "on");
    model.result().export("anim1").set("showgrid", "on");
    model.result().export("anim1").set("plotgroup", "pg3");
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 2219, 0);
    model.result("pg3").setIndex("looplevel", 760, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 815, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 1892, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 1895, 0);
    model.result("pg3").setIndex("looplevel", 1283, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 1633, 0);
    model.result("pg3").run();

    model.study("std2").feature("time").set("tlist", "range(0,1e-6,2e-4)");

    model.result("pg3").run();

    model.component("comp1").physics("cpt").feature("pbeam1").set("N", 1000);

    model.sol("sol2").runAll();

    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 141, 0);
    model.result("pg3").run();
    model.result("pg3").setIndex("looplevel", 200, 0);
    model.result("pg3").run();

    model.label("lens8newMCP_ks_v2_multi_flange_config_11_2.mph");

    model.result("pg3").run();

    model.study("std2").feature("time").set("tlist", "range(0,5e-7,2e-4)");

    model.sol("sol2").runAll();

    model.result("pg3").run();

    model.label("lens8newMCP_ks_v2_multi_flange_config_11_2.mph");

    model.result("pg3").run();

    return model;
  }

  public static void main(String[] args) {
    Model model = run();
    model = run2(model);
    model = run3(model);
    model = run4(model);
    model = run5(model);
    model = run6(model);
    model = run7(model);
    model = run8(model);
    model = run9(model);
    model = run10(model);
    model = run11(model);
    model = run12(model);
    model = run13(model);
    model = run14(model);
    model = run15(model);
    model = run16(model);
    model = run17(model);
    model = run18(model);
    run19(model);
  }

}
