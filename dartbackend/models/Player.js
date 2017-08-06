var mongoose = require('mongoose');
var RoundSchema = new mongoose.Schema({
  value: Number,
  multi: Number
});
var PlayerSchema = new mongoose.Schema({
  name: String,
  average: Number,
  highfinish: Number,
  onehundredandeighty: Number,
  doppelquote: Number,
  wins: Number,
  points: { type: Number, default: 0 },
  round: [RoundSchema],
  turn: {type: Boolean, default: false},
  updated_at: { type: Date, default: Date.now },
});
module.exports = mongoose.model('Player', PlayerSchema);

