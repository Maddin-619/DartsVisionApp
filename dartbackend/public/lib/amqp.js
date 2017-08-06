(function() {
  var AmqpConnection, amqp, gui, uuid,
    __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; };

  //amqp = require('amqplib/callback_api');

  uuid = require("uuid");

  gui = require("nw.gui");

  AmqpConnection = (function() {
    function AmqpConnection(handler) {
      var _this = this;
      this.handler = handler;
      this.stopHeartbeat = __bind(this.stopHeartbeat, this);
      this.startHeartbeat = __bind(this.startHeartbeat, this);
      this.receive = __bind(this.receive, this);
      this.publish = __bind(this.publish, this);
      this.connection = amqp.createConnection({
        host: "localhost",
        login: "guest",
        password: "guest"
      });
      this.connection.on("ready", function() {
        _this.queue_name = uuid.v4();
        gui.Window.get().on("close", function() {
          return _this.connection.end();
        });
        return _this.connection.queue(_this.queue_name, function(q) {
          _this.q = q;
          _this.q.bind("#");
          return _this.q.subscribe(_this.receive);
        });
      });
    }

    AmqpConnection.prototype.publish = function(message, headers) {
      headers = headers != null ? headers : {};
      headers.sent = new Date().getTime();
      return this.connection.publish(this.queue_name, message, {
        headers: headers,
        contentType: "application/json"
      });
    };

    AmqpConnection.prototype.receive = function(msg, headers, deliveryInfo) {
      var message;
      headers.received = new Date().getTime();
      message = {
        headers: headers,
        body: msg
      };
      return this.handler(message);
    };

    AmqpConnection.prototype.startHeartbeat = function(interval) {
      var sendHeartbeat,
        _this = this;
      interval = interval != null ? interval : 1500;
      sendHeartbeat = function() {
        return _this.publish({
          ping: "pong!"
        });
      };
      return this.heartbeat_handle = setInterval(sendHeartbeat, interval);
    };

    AmqpConnection.prototype.stopHeartbeat = function() {
      if (this.heartbeat_handle != null) {
        return clearInterval(this.heartbeat_handle);
      }
    };

    return AmqpConnection;

  })();

  window.AmqpConnection = AmqpConnection;

}).call(this);