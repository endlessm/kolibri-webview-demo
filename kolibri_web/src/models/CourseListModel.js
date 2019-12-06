import { observable, computed, action } from "mobx";

import CourseModel from "./CourseModel";

export default class CourseListModel {
    @observable courses = [];

    @computed
    get coursesCount() {
      return this.courses.length;
    }

    @action
    addCourse(id, name) {
      this.courses.push(new CourseModel(id, name));
    }
}
