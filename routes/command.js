var express = require('express');
var router = express.Router();

router.get('/', function (req, res, next) {
  if (req.query.switch == 'true') {
    console.log('light on');
    global.channel.sendToQueue('task',new Buffer('light_on'),{persistent: true, deliveryMode: 2});
    res.send('light on');
  } else if (req.query.switch == 'false') {
    console.log('light off');
    global.channel.sendToQueue('task',new Buffer('light_off'),{persistent: true, deliveryMode: 2});
    res.send('light off');
  } else if (req.query.game == 'true') {
    console.log('game on');
    global.channel.sendToQueue('task',new Buffer('game_on'),{persistent: true, deliveryMode: 2});
    res.send('game on');
  }else if (req.query.game == 'false') {
    console.log('game off');
    global.channel.sendToQueue('task',new Buffer('game_off'),{persistent: true, deliveryMode: 2});
    res.send('game off');
  }
});

module.exports = router;
