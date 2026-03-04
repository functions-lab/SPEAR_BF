# Definitional proc to organize widgets for parameters.
proc init_gui { IPINST } {
  ipgui::add_param $IPINST -name "Component_Name"
  #Adding Page
  ipgui::add_page $IPINST -name "Page 0"

  ipgui::add_param $IPINST -name "AXIS_TDATA_WIDTH" -widget comboBox
  ipgui::add_param $IPINST -name "NUM_CH" -widget comboBox

}

proc update_PARAM_VALUE.AXIS_TDATA_WIDTH { PARAM_VALUE.AXIS_TDATA_WIDTH } {
	# Procedure called to update AXIS_TDATA_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.AXIS_TDATA_WIDTH { PARAM_VALUE.AXIS_TDATA_WIDTH } {
	# Procedure called to validate AXIS_TDATA_WIDTH
	return true
}

proc update_PARAM_VALUE.NUM_CH { PARAM_VALUE.NUM_CH } {
	# Procedure called to update NUM_CH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.NUM_CH { PARAM_VALUE.NUM_CH } {
	# Procedure called to validate NUM_CH
	return true
}


proc update_MODELPARAM_VALUE.NUM_CH { MODELPARAM_VALUE.NUM_CH PARAM_VALUE.NUM_CH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.NUM_CH}] ${MODELPARAM_VALUE.NUM_CH}
}

proc update_MODELPARAM_VALUE.AXIS_TDATA_WIDTH { MODELPARAM_VALUE.AXIS_TDATA_WIDTH PARAM_VALUE.AXIS_TDATA_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.AXIS_TDATA_WIDTH}] ${MODELPARAM_VALUE.AXIS_TDATA_WIDTH}
}

