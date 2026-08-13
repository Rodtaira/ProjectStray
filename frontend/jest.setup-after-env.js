const { configure } = require('@testing-library/react-native');

// Cold-start (babel transform, module init) on the first test in a suite can
// take several seconds under parallel worker contention — give waitFor and
// the overall test both enough room so that isn't mistaken for a hang.
configure({ asyncUtilTimeout: 15000 });
jest.setTimeout(20000);
