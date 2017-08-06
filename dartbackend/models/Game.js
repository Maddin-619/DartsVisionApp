var mongoose = require('mongoose')
  , Schema = mongoose.Schema
var GameSchema = new mongoose.Schema({
  gamepoints: Number,
  doublein: Boolean,
  doubleout: Boolean,
  elimination: Boolean,
  players: [{ type : Schema.Types.ObjectId, ref: 'Player' }]
});
module.exports = mongoose.model('Game', GameSchema);

