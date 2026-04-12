import { NextRequest, NextResponse } from 'next/server';
import { getProject, updateProject } from '../storage';

// GET project (public)
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const project = await getProject(params.id);

    if (!project) {
      return NextResponse.json(
        { error: 'Project not found' },
        { status: 404 }
      );
    }

    return NextResponse.json(project);
  } catch (error) {
    console.error('Failed to get project:', error);

    return NextResponse.json(
      { error: 'Failed to get project' },
      { status: 500 }
    );
  }
}

// UPDATE project (public)
export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const contentType = request.headers.get('content-type');

    if (!contentType || !contentType.includes('application/json')) {
      return NextResponse.json(
        { error: 'Content-Type must be application/json' },
        { status: 400 }
      );
    }

    const body = await request.json();

    const project = await getProject(params.id);

    if (!project) {
      return NextResponse.json(
        { error: 'Project not found' },
        { status: 404 }
      );
    }

    const updatedProject = await updateProject(params.id, body);

    if (!updatedProject) {
      return NextResponse.json(
        { error: 'Failed to update project' },
        { status: 500 }
      );
    }

    return NextResponse.json(updatedProject);
  } catch (error) {
    console.error('Failed to update project:', error);

    return NextResponse.json(
      { error: 'Failed to update project' },
      { status: 500 }
    );
  }
}
