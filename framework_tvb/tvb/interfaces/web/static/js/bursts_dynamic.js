/**
 * TheVirtualBrain-Framework Package. This package holds all Data Management, and
 * Web-UI helpful to run brain-simulations. To use it, you also need do download
 * TheVirtualBrain-Scientific Package (for simulators). See content of the
 * documentation-folder for more details. See also http://www.thevirtualbrain.org
 *
 * (c) 2012-2013, Baycrest Centre for Geriatric Care ("Baycrest")
 *
 * This program is free software; you can redistribute it and/or modify it under
 * the terms of the GNU General Public License version 2 as published by the Free
 * Software Foundation. This program is distributed in the hope that it will be
 * useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
 * License for more details. You should have received a copy of the GNU General
 * Public License along with this program; if not, you can download it here
 * http://www.gnu.org/licenses/old-licenses/gpl-2.
 *
 *   CITATION:
 * When using The Virtual Brain for scientific publications, please cite it as follows:
 *
 *   Paula Sanz Leon, Stuart A. Knock, M. Marmaduke Woodman, Lia Domide,
 *   Jochen Mersmann, Anthony R. McIntosh, Viktor Jirsa (2013)
 *       The Virtual Brain: a simulator of primate brain network dynamics.
 *   Frontiers in Neuroinformatics (7:10. doi: 10.3389/fninf.2013.00010)
 *
 * .. moduleauthor:: Mihai Andrei <mihai.andrei@codemart.ro>
 **/

/* globals doAjaxCall, displayMessage, MathJax, getSubmitableData */

var dynamicPage = {
    treeState: {},      // the state of the left input tree. Used to detect changes
    dynamic_gid: null
};

/** @module ui components module */
(function(){
    /**
     * Handles events for a group of sliders
     * @constructor
     */
    function SliderGroup(states, resetBtn, onChange){
        var self = this;
        self.onChange = onChange;
        self.states = states;
        for (var i = 0; i < states.length; i++){
            self._initSlider(states[i]);
        }
        $(resetBtn).click(function(){ self.reset(); });
    }

    SliderGroup.prototype._initSlider = function(option){
        var self = this;
        var slider = $("#slider_" + option.name);
        var input = $("#value_" + option.name);

        slider.slider({
            value: option.default,
            min: option.min,
            max: option.max,
            step: option.step,

            slide: function(ev, target) {
                input.val(target.value);
            },

            change: function(ev, target){
                input.val(target.value);
                self.onChange(option.name, target.value);
            }
        });

        input.change(function(){
            var val = parseFloat(input.val());
            if (isNaN(val) || val < option.min || val > option.max){
                val = option.default;
            }
            slider.slider('value', val);
        }).click(function(){
            input.select();
        });
    };

    SliderGroup.prototype.reset = function(){
        for (var i = 0; i < this.states.length; i++) {
            var option = this.states[i];
            var slider = $("#slider_" + option.name);
            slider.slider('value', option.default);
        }
    };

    SliderGroup.prototype.getValues = function(){
        var name2val = {};
        for (var i = 0; i < this.states.length; i++) {
            var option = this.states[i];
            var slider = $("#slider_" + option.name);
            name2val[option.name] = slider.slider('value');
        }
        return name2val;
    };

    SliderGroup.prototype.hide = function(sv_to_disable){
        for (var i = 0; i < this.states.length; i++) {
            var option = this.states[i];
            var slider = $("#slider_" + option.name);
            var input = $("#value_" + option.name);
            var enabled = sv_to_disable.indexOf(option.name) === -1;

            slider.slider(enabled? 'enable':'disable');
            input.toggle(enabled);
        }
    };

    /**
     * @constructor
     */
    function AxisControls(state, svDrop, slider, span, onChange){
        var self = this;
        self.onChange = onChange;
        self.state = state;
        self.$sv = $(svDrop);
        self.$slider = $(slider);
        self.$span = $(span);

        self.$sv.change(function(){
            self.val(self.$sv.val());
            onChange();
        });

        self.$slider.slider({
            range:true,
            slide: function(ev, target) {
                self._updateSpan(target.values);
            },
            change : function(ev, target){
                self._updateSpan(target.values);
                self.onChange();
            }
        });
    }

    AxisControls.prototype._getStateVarByName = function(name){
        return $.grep(this.state.state_variables, function(n){
            return n.name === name;
        })[0];
    };

    AxisControls.prototype._updateSpan = function(r){
        this.$span.text(r[0] + ' .. ' + r[1]);
    };

    AxisControls.prototype.val = function(sv){
        if (sv == null) {
            return {sv: this.$sv.val(), range: this.$slider.slider('values')};
        }else{
            var opt = this._getStateVarByName(sv);
            this.$sv.val(sv);
            this.$slider.slider({ min: opt.min, max: opt.max, values: [opt.lo, opt.hi], step: (opt.max - opt.min)/1000 });
            this._updateSpan([opt.lo, opt.hi]);
        }
    };


    /**
     * Dom selectors are hard coded so only one instance makes sense.
     * deprecated: move logic to plane controller
     * @constructor
     */
    function AxisGroup(state, onChange){
        var self = this;
        self.onChange = onChange;
        self.state = state;
        self.$mode = $('#mode');
        self.ax = new AxisControls(state, '#svx', '#slider_x_axis', '#x_range_span', onChange);
        self.ay = new AxisControls(state, '#svy', '#slider_y_axis', '#y_range_span', onChange);
        self.ax.val(this.state.default_sv[0]);
        self.ay.val(this.state.default_sv[1]);
        self.$mode.change(onChange);
        $('#reset_axes').click(function() { self.reset();});
    }

    AxisGroup.prototype.reset = function(){
        this.$mode.val(this.state.default_mode);
        this.ax.val(this.state.default_sv[0]);
        this.ay.val(this.state.default_sv[1]);
    };

    AxisGroup.prototype.getValue = function(){
        var axv = this.ax.val();
        var ayv = this.ay.val();
        return {
            mode: this.$mode.val(),
            svx: axv.sv, svy: ayv.sv,
            x_range: axv.range, y_range: ayv.range
        };
    };

    dynamicPage.SliderGroup = SliderGroup;
    dynamicPage.AxisGroup = AxisGroup;
    dynamicPage.AxisControls = AxisControls;
})();


/** @module main */
(function(){

var DEBOUNCE_DELAY = 25;

function _url(func, tail){
    var url = '/burst/dynamic/' + func + '/' + dynamicPage.dynamic_gid;
    if (tail != null){
        url+= '/' + tail;
    }
    return url;
}

/**
 * Server connected phase view.
 * Handles graph state and trajectories.
 * @constructor
 */
function PhasePlaneController(graph_defaults, phasePlane) {
    var self = this;
    this.graph_defaults = graph_defaults;  // information about the graph: shown state variables, state variable and axis ranges
    this.traj_starts = [];                 // trajectory starting points. Kept to resubmit trajectory computation if model params change
    // the trajectories/signals raw data.
    // It is idiomatic in d3 not to draw incrementally but to update the data set.
    // Thus we keep the dataset because we have to update if a new traj is added.
    this.trajectories = [];
    this.phasePlane = phasePlane;
    // see onParameterChanged
    var onGraphChanged = $.debounce(DEBOUNCE_DELAY, function(){self._onGraphChanged();});
    this.stateVarsSliders = new dynamicPage.SliderGroup(graph_defaults.state_variables, '#reset_state_variables', onGraphChanged);
    this.axisControls = new dynamicPage.AxisGroup(graph_defaults, onGraphChanged);
    $('#reset_trajectories').click(function(){self._deleteTrajectories();});
    //clear all trajectories
    this._deleteTrajectories();
    this._disable_active_sv_slider();
    // xxx work in progress
}

PhasePlaneController.prototype._redrawPhasePlane = function(data){
    data = JSON.parse(data);
    this.phasePlane.draw(data);
    var axis_state = this.axisControls.getValue();
    this.phasePlane.setLabels(axis_state.svx, axis_state.svy);
    this.phasePlane.setPlotLabels($.map(this.graph_defaults.state_variables, function(d){return d.name;}) );
};

PhasePlaneController.prototype._disable_active_sv_slider = function(){
    var axis_state = this.axisControls.getValue();
    this.stateVarsSliders.hide([axis_state.svx, axis_state.svy]);
};

PhasePlaneController.prototype._onGraphChanged = function(){
    var self = this;
    var axis_state = this.axisControls.getValue();
    axis_state.state_vars = this.stateVarsSliders.getValues();
    this._disable_active_sv_slider();
    doAjaxCall({
        url: _url('graph_changed'),
        data: { graph_state: JSON.stringify(axis_state)},
        success : function(data){
            self._redrawPhasePlane(data);
            self._redrawTrajectories();
        }
    });
};

PhasePlaneController.prototype._deleteTrajectories = function(){
    this.trajectories = [];
    this.traj_starts = [];
    this.phasePlane.drawTrajectories([]);
    this.phasePlane.drawSignal([]);
};

function _trajectories_rpc(starting_points, success){
    doAjaxCall({
        url: _url('trajectories'),
        data: {starting_points: JSON.stringify(starting_points)},
        success:function(data){
            data = JSON.parse(data);
            if (data.finite) {
                success(data);
            }else{
                displayMessage('Trajectory contains infinities. Try to decrease the integration step.', 'warningMessage');
            }
        }
    });
}

PhasePlaneController.prototype._redrawTrajectories = function(){
    var self = this;
    if (this.traj_starts.length === 0){
        return;
    }
    _trajectories_rpc(this.traj_starts, function(data){
        self.trajectories = data.trajectories;
        self.phasePlane.drawTrajectories(self.trajectories);
        self.phasePlane.drawSignal(data.signals);
    });
};

function _fetchSlidersFromServer(paramDefaults, graphDefaults){
    var sliderContainer = $('#div_spatial_model_params');
    sliderContainer.empty();

    doAjaxCall({
        url: _url('sliders_fragment'),
        success: function(fragment) {
            sliderContainer.html(fragment);
            MathJax.Hub.Queue(["Typeset", MathJax.Hub, 'div_spatial_model_params']);
            setupMenuEvents(sliderContainer);
            dynamicPage.grafic = new PhasePlaneController(graphDefaults, dynamicPage.phasePlane);

            dynamicPage.paramSliders = new dynamicPage.SliderGroup(paramDefaults, '#reset_sliders', onParameterChanged);

            _onParameterChanged();
        }
    });
}

function onModelChanged(name){
    doAjaxCall({
        url: _url('model_changed', name) ,
        success: function(data){
            data = JSON.parse(data);
            _fetchSlidersFromServer(data.params, data.graph_params);
        }
    });
}


function _onParameterChanged(){
    doAjaxCall({
        url: _url('parameters_changed'),
        data: {params: JSON.stringify(dynamicPage.paramSliders.getValues())},
        success : function(data){
            dynamicPage.grafic._redrawPhasePlane(data);
            dynamicPage.grafic._redrawTrajectories();
        }
    });
}

// Resetting a slider group will trigger change events for each slider. The handler does a slow ajax so debounce the handler
var onParameterChanged = $.debounce(DEBOUNCE_DELAY, _onParameterChanged);


function onTrajectory(x, y){
    var start_state = dynamicPage.grafic.stateVarsSliders.getValues();
    var axis_state = dynamicPage.grafic.axisControls.getValue();
    start_state[axis_state.svx] = x;
    start_state[axis_state.svy] = y;

    _trajectories_rpc([start_state], function(data){
        dynamicPage.grafic.traj_starts.push(start_state);
        dynamicPage.grafic.trajectories.push(data.trajectories[0]);
        dynamicPage.phasePlane.drawTrajectories(dynamicPage.grafic.trajectories);
        dynamicPage.phasePlane.drawSignal(data.signals);
    });
}


// Throttle the rate of trajectory creation. In a burst of mouse clicks some will be ignored.
// Ignore trailing events. Without this throttling the server overwhelms and numexpr occasionally segfaults.
var onTrajectory = $.throttle(500, true, onTrajectory);

function onSubmit(event){
    var name = $('#dynamic_name').val().trim();
    if (name.length ) {
        doAjaxCall({
            url: _url('submit', name),
            success: function(){
                displayMessage('Dynamic saved', 'importantMessage');
            }
        });
    }else{
        displayMessage('A name is required', 'errorMessage');
    }
    event.preventDefault();
}

function onIntegratorChanged(state){
    doAjaxCall({
        url: _url('integrator_changed'),
        data: state,
        success: function(){dynamicPage.grafic._redrawTrajectories();}
    });
}

// Event debouncing makes less sense now that the requests have been made blocking.
var debouncedOnIntegratorChanged = $.debounce( DEBOUNCE_DELAY, onIntegratorChanged);

// Detect changes by doing a tree diff. This diff is simple but relies on a specific tree structure.
function onTreeChange(){
    var state = getSubmitableData('left_input_tree');
    var previous = dynamicPage.treeState;
    if (state.model_type !== previous.model_type){
        onModelChanged(state.model_type);
    }else if (state.dynamic_name === previous.dynamic_name){
        // Name has not changed. The change is in the integrator subtree
        debouncedOnIntegratorChanged(state);
    }
    dynamicPage.treeState = state;
}

function main(dynamic_gid){
    dynamicPage.dynamic_gid = dynamic_gid;
    $('.field-adapters').hide(); // hide expand range buttons. Careful as this class is used for other things as well
    // listen for changes of the left tree
    $('#left_input_tree').find('input').add('select').change(onTreeChange);
    $('#base_spatio_temporal_form').submit(onSubmit);
    onTreeChange();
    dynamicPage.phasePlane = new TVBUI.PhasePlane('#phasePlane');
    dynamicPage.phasePlane.onClick = onTrajectory;
}

dynamicPage.main = main;

})();
