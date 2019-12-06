import React from "react";
import { observer } from "mobx-react";

@observer
class CourseList extends React.Component {
	render() {
		return (
			<div>
				<hr />
				<ul>
					{this.props.store.courses.map(course => (
                        <li key={course.id}>{course.name}</li>
					))}
				</ul>
			</div>
		);
	}
}

export default CourseList;
