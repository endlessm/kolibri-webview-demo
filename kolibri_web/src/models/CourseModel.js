import { observable } from "mobx";

export default class CourseModel {
    id = null;

    @observable name;

    constructor(id, name) {
        this.id = id;
        this.name = name;
    }
}
