import React from "react";
import { render } from "react-dom";
import DevTools from "mobx-react-devtools";

import CourseList from "./components/CourseList";
import CourseListModel from "./models/CourseListModel";

const store = new CourseListModel();

render(
  <div>
    <DevTools />
    <CourseList store={store} />
  </div>,
  document.getElementById("root")
);

store.addCourse('0', "Rocket science for beginners");

setTimeout(() => {
  store.addCourse('1', "How to make tea");
}, 2000);

// playing around in the console
window.store = store;
