import { NextRequest, NextResponse } from 'next/server';
import { getAllProjects, createProject, deleteProject } from './storage';

// CREATE project
export async function POST(request: NextRequest) {
  try {
    const contentType = request.headers.get('content-type');

    if (!contentType || !contentType.includes('application/json')) {
      return NextResponse.json(
        { error: 'Content-Type must be application/json' },
        { status: 400 }
      );
    }

    const body = await request.json();
    const { name, path } = body;

    if (!name || !path) {
      return NextResponse.json(
        { error: 'Name and path are required' },
        { status: 400 }
      );
    }

    const project = await createProject(name, path);

    return NextResponse.json(project);
  } catch (error) {
    console.error('Failed to create project:', error);

    return NextResponse.json(
      { error: 'Failed to create project' },
      { status: 500 }
    );
  }
}

// GET all projects
export async function GET() {
  try {
    const projects = await getAllProjects();
    return NextResponse.json(projects);
  } catch (error) {
    console.error('Failed to get projects:', error);

    return NextResponse.json(
      { error: 'Failed to get projects' },
      { status: 500 }
    );
  }
}

// DELETE project
export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const projectId = searchParams.get('id');

    if (!projectId) {
      return NextResponse.json(
        { error: 'Project ID is required' },
        { status: 400 }
      );
    }

    const deleted = await deleteProject(projectId);

    if (!deleted) {
      return NextResponse.json(
        { error: 'Project not found' },
        { status: 404 }
      );
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Failed to delete project:', error);

    return NextResponse.json(
      { error: 'Failed to delete project' },
      { status: 500 }
    );
  }
}
