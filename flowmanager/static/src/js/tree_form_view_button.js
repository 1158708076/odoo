odoo.define('flowmanager.tree_form_view_button', function (require) {
    "use strict";

    var Form = require('web.FormView');
    var FormController = require('web.FormController');
    var viewRegistry = require('web.view_registry');
    var rpc = require('web.rpc');
    var FormRenderer = require('web.FormRenderer');
    var Dialog = require('web.Dialog');

    var flowmanagerFormController = FormController.extend({
        approve_btn_template: 'flowmanagerForm.approve_btn',
        /**
         * Extends the renderButtons function of ListView by adding an event listener
         * on the bill upload button.
         *
         * @override
         */
        renderButtons: function () {
            this._super.apply(this, arguments);
        },
    });

    var flowmanagerFormViewRender = FormRenderer.extend({

        /**
         * @private
         * @param {Object} node
         * @returns {jQueryElement}
         */
        _renderHeaderButton: function (node) {
            var self = this;
            console.log("保证每次都会刷新_render_render_render_render_render", this);
            console.log("再次确认获取的内容", self);
            console.log("再次确认获取到的内容：", self.state.data, self.state.context, self.state.data.x_oa_resourceflow, self.state.data.x_oa_state);
            var modelname = self.state.model;
            // var res_id = this.state.res_id;
            var context = self.state.context;
            var flow = self.state.data.x_oa_resourceflow;
            var flowstate = self.state.data.x_oa_state;
            console.log("再次确认获取到的内容：", modelname, context, flow, flowstate);
            rpc.query({
                model: 'oa',
                method: 'get_all_ordertype_model_name',
                args: [context],
            }).then(function (data) {
                //如果相等，表明流程绑定了表单，则可展示流程的按钮
                if (data.indexOf(modelname) != -1) {
                    if (flow != false) {
                        console.log("提交过的_render")
                        console.log(flowstate)
                        if ('nosubmit' == flowstate || 'termination' == flowstate) {
                            console.log(flowstate + "_render1")
                            $('.o_form_tender_button_commit').css("visibility", "visible");
                            $('.o_form_tender_button_approval').css("visibility", "hidden");
                            $('.o_form_tender_button_reject').css("visibility", "hidden");
                            // $('.o_form_tender_button_rejectTo').css("visibility", "hidden");
                            $('.o_form_tender_button_approve_termination').css("visibility", "hidden");
                        } else if ('ok' == flowstate) {
                            $('.o_form_tender_button_commit').css("visibility", "hidden");
                            $('.o_form_tender_button_approval').css("visibility", "hidden");
                            $('.o_form_tender_button_reject').css("visibility", "hidden");
                            // $('.o_form_tender_button_rejectTo').css("visibility", "hidden");
                            $('.o_form_tender_button_approve_termination').css("visibility", "hidden");
                        } else {
                            console.log(flowstate + "_render2")
                            $('.o_form_tender_button_commit').css("visibility", "hidden");
                            $('.o_form_tender_button_approval').css("visibility", "visible");
                            $('.o_form_tender_button_reject').css("visibility", "visible");
                            // $('.o_form_tender_button_rejectTo').css("visibility", "visible");
                            $('.o_form_tender_button_approve_termination').css("visibility", "visible");
                        }
                    } else {
                        console.log("没有提交过的_render")
                        $('.o_form_tender_button_commit').css("visibility", "visible");
                        $('.o_form_tender_button_approval').css("visibility", "hidden");
                        $('.o_form_tender_button_reject').css("visibility", "hidden");
                        // $('.o_form_tender_button_rejectTo').css("visibility", "hidden");
                        $('.o_form_tender_button_approve_termination').css("visibility", "hidden");
                    }
                }
                $('.o_form_tender_button_commit').on('click', self.proxy('approve_commit'));//提交
                $('.o_form_tender_button_approval').on('click', self.proxy('approve_next'));//批准
                $('.o_form_tender_button_reject').on('click', self.proxy('reject_next'));//驳回
                // $('.o_form_tender_button_rejectTo').on('click', self.proxy('reject_to'));//驳回至
                $('.o_form_tender_button_approve_termination').on('click', self.proxy('approve_termination'));//审批终止
            });

            return this._super.apply(this, arguments);
        },

        // _renderButtonBox: function (node) {
        //     var self = this;
        //     console.log("保证每次都会刷新_render_render_render_render_render", this);
        //     console.log("再次确认获取的内容", self);
        //     console.log("再次确认获取到的内容：", self.state.data, self.state.context, self.state.data.x_oa_resourceflow, self.state.data.x_oa_state);
        //     var modelname = self.state.model;
        //     // var res_id = this.state.res_id;
        //     var context = self.state.context;
        //     var flow = self.state.data.x_oa_resourceflow;
        //     var flowstate = self.state.data.x_oa_state;
        //     console.log("再次确认获取到的内容：", modelname, context, flow, flowstate);
        //     rpc.query({
        //         model: 'oa',
        //         method: 'get_all_ordertype_model_name',
        //         args: [context],
        //     }).then(function (data) {
        //         //如果相等，表明流程绑定了表单，则可展示流程的按钮
        //         if (data.indexOf(modelname) != -1) {
        //             if (flow != false) {
        //                 console.log("提交过的_render")
        //                 console.log(flowstate)
        //                 if ('nosubmit' == flowstate) {
        //                     console.log(flowstate + "_render1")
        //                     $('.o_form_tender_button_commit').css("visibility", "visible");
        //                     $('.o_form_tender_button_approval').css("visibility", "hidden");
        //                     $('.o_form_tender_button_reject').css("visibility", "hidden");
        //                     // $('.o_form_tender_button_rejectTo').css("visibility", "hidden");
        //                     $('.o_form_tender_button_approve_termination').css("visibility", "hidden");
        //                 } else if ('ok' == flowstate || 'termination' == flowstate) {
        //                     $('.o_form_tender_button_commit').css("visibility", "hidden");
        //                     $('.o_form_tender_button_approval').css("visibility", "hidden");
        //                     $('.o_form_tender_button_reject').css("visibility", "hidden");
        //                     // $('.o_form_tender_button_rejectTo').css("visibility", "hidden");
        //                     $('.o_form_tender_button_approve_termination').css("visibility", "hidden");
        //                 } else {
        //                     console.log(flowstate + "_render2")
        //                     $('.o_form_tender_button_commit').css("visibility", "hidden");
        //                     $('.o_form_tender_button_approval').css("visibility", "visible");
        //                     $('.o_form_tender_button_reject').css("visibility", "visible");
        //                     // $('.o_form_tender_button_rejectTo').css("visibility", "visible");
        //                     $('.o_form_tender_button_approve_termination').css("visibility", "visible");
        //                 }
        //             } else {
        //                 console.log("没有提交过的_render")
        //                 $('.o_form_tender_button_commit').css("visibility", "visible");
        //                 $('.o_form_tender_button_approval').css("visibility", "hidden");
        //                 $('.o_form_tender_button_reject').css("visibility", "hidden");
        //                 // $('.o_form_tender_button_rejectTo').css("visibility", "hidden");
        //                 $('.o_form_tender_button_approve_termination').css("visibility", "hidden");
        //             }
        //         }
        //         $('.o_form_tender_button_commit').on('click', self.proxy('approve_commit'));//提交
        //         $('.o_form_tender_button_approval').on('click', self.proxy('approve_next'));//批准
        //         $('.o_form_tender_button_reject').on('click', self.proxy('reject_next'));//驳回
        //         // $('.o_form_tender_button_rejectTo').on('click', self.proxy('reject_to'));//驳回至
        //         $('.o_form_tender_button_approve_termination').on('click', self.proxy('approve_termination'));//审批终止
        //     });
        //     return this._super.apply(this, arguments);
        // },

        /**
         * 实现自定义按钮的事件
         * tb.odoo是我model名称，tb_odoo_tong是我的方法名称。
         *
         */

        approve_commit: function (event) {
            if (!event.isPropagationStopped()) {
                console.log('我要提交了：' + this);
                console.log("（提交）这是必要的参数：" + this.state.context, this.state.res_id, this.state.model);
                rpc.query({
                    model: 'oa',
                    method: 'otherorder_commit',
                    args: [this.state.context, this.state.res_id, this.state.model],
                }).then(function (data) {
                    console.log('我要提交了，之后返回的参数：' + data);
                    if (data != null) {
                        Dialog.alert(this, data.warning.message, {
                            title: data.warning.title,
                        });
                    } else {
                        location.reload();
                    }
                });
            }
            //执行点击后要执行的代码
            event.stopPropagation();
        },
        approve_next: function (event) {
            if (!event.isPropagationStopped()) {
                console.log('我要审批了：' + this);
                console.log("（审批）这是必要的参数：" + this.state.context, this.state.res_id, this.state.model);
                rpc.query({
                    model: 'oa',
                    method: 'action_approval_js',
                    args: [this.state.context, this.state.data.x_oa_resourceflow.res_id],
                }).then(function (data) {
                    console.log('我要审批了，之后返回的参数：' + data);
                    if (data != null) {
                        Dialog.alert(this, data.warning.message, {
                            title: data.warning.title,
                        });
                    } else {
                        location.reload();
                    }
                });
            }
            //执行点击后要执行的代码
            event.stopPropagation();
        },
        reject_next: function (event) {
            if (!event.isPropagationStopped()) {
                console.log('我要驳回了：' + this);
                console.log("（驳回）这是必要的参数：" + this.state.context, this.state.res_id, this.state.model);
                this.do_action({
                    name: '进行驳回处理',
                    res_model: 'oa.flow.step',
                    views: [[false, 'form']],
                    type: 'ir.actions.act_window',
                    target: 'new',
                    context: {
                        default_step_lvid: this.state.data.x_oa_resourceflow.res_id,
                    },
                }, {
                    on_close: function () {
                        location.reload();
                    },
                });
            }
            //执行点击后要执行的代码
            event.stopPropagation();
        },
        // reject_to: function () {
        //     console.log('我要驳回至了：' + this);
        //     console.log("（驳回至）这是必要的参数：" + this.state.context, this.state.res_id, this.state.model);
        //     location.reload();
        // },
        approve_termination: function (event) {
            if (!event.isPropagationStopped()) {
                console.log('我要终止审批了：' + this);
                console.log("（终止审批）这是必要的参数：" + this.state.context, this.state.res_id, this.state.model);
                rpc.query({
                    model: 'oa',
                    method: 'action_approve_termination_js',
                    args: [this.state.context, this.state.data.x_oa_resourceflow.res_id],
                }).then(function (data) {
                    if (data != null) {
                        Dialog.alert(this, data.warning.message, {
                            title: data.warning.title,
                        });
                    } else {
                        location.reload();
                    }
                });
            }
            //执行点击后要执行的代码
            event.stopPropagation();
        },

    });


    var flowmanagerFormView = Form.extend({
        config: _.extend({}, Form.prototype.config, {
            Renderer: flowmanagerFormViewRender,
            Controller: flowmanagerFormController,
        }),

        /**
         * Returns the a new view renderer instance
         *
         * @param {Widget} parent the parent of the model, if it has to be created
         * @param {Object} state the information related to the rendered view
         * @return {Object} instance of the view renderer
         */
        getRenderer: function (parent, state) {
            return new flowmanagerFormViewRender(parent, state, this.rendererParams);
        },

    });

    viewRegistry.add('tree_form_view_button', flowmanagerFormView);
    return {
        Renderer: flowmanagerFormViewRender,
        Controller: flowmanagerFormController,
    };
});