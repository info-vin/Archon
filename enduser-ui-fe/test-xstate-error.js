import { setup, assign, fromPromise, createActor } from 'xstate';

const m = setup({
  actors: {
    fetch: fromPromise(async () => { throw new Error("API failed"); })
  }
}).createMachine({
  initial: 'loading',
  context: { error: null },
  states: {
    loading: {
      invoke: {
        src: 'fetch',
        onError: {
          target: 'error',
          actions: assign({
            error: ({ event }) => event.error?.message || 'Unknown error'
          })
        }
      }
    },
    error: {}
  }
});

const actor = createActor(m);
actor.subscribe(s => console.log(s.value, s.context));
actor.start();
