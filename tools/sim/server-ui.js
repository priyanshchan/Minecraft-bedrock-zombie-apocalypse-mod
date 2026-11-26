// A stand-in for @minecraft/server-ui: forms answer from scripted responses (undefined = closed).
export const answers = [];
export const shown = [];
export const FormCancelationReason = { UserBusy: "UserBusy", UserClosed: "UserClosed" };

function respond(kind, info) {
  shown.push({ kind, ...info });
  const a = answers.shift();
  if (a === undefined) return Promise.resolve({ canceled: true, cancelationReason: FormCancelationReason.UserClosed });
  if (kind === "modal") return Promise.resolve({ canceled: false, formValues: a });
  return Promise.resolve({ canceled: false, selection: a });
}

export class ActionFormData {
  constructor() { this.buttons = []; }
  title(t) { this.t = t; return this; }
  body(b) { this.b = b; return this; }
  button(t) { this.buttons.push(t); return this; }
  label() { return this; }
  header() { return this; }
  divider() { return this; }
  show() { return respond("action", { title: this.t, body: this.b, buttons: this.buttons }); }
}
export class MessageFormData {
  title(t) { this.t = t; return this; }
  body(b) { this.b = b; return this; }
  button1() { return this; }
  button2() { return this; }
  show() { return respond("message", { title: this.t }); }
}
export class ModalFormData {
  constructor() { this.fields = []; }
  title(t) { this.t = t; return this; }
  label() { return this; }
  dropdown(l) { this.fields.push(l); return this; }
  toggle(l) { this.fields.push(l); return this; }
  slider(l) { this.fields.push(l); return this; }
  textField(l) { this.fields.push(l); return this; }
  show() { return respond("modal", { title: this.t, fields: this.fields }); }
}
