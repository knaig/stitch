import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import ChatAndVideo from './ChatAndVideo';  // Import the new component

function App() {
  return (
    <Router>
      <Switch>
        <Route path="/" exact component={ChatAndVideo} />  {/* Default route to ChatAndVideo */}
        {/* Add more routes here as your app grows */}
      </Switch>
    </Router>
  );
}

export default App;
